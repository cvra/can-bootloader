import serial
import socket
import argparse
import time

from cvra_bootloader import commands
import can
import logging
import can.adapters

from collections import defaultdict

class ConnectionArgumentParser(argparse.ArgumentParser):
    """
    Subclass of ArgumentParser with default arguments for connection handling (TCP and serial).

    It also checks that the user provides at least one connection method (--tcp or --port).
    """

    def __init__(self, *args, **kwargs):
        super(ConnectionArgumentParser, self).__init__(*args, **kwargs)

        self.add_argument('-p', '--port', dest='serial_device',
                          help='Serial port to which the CAN bridge is connected to.',
                          metavar='DEVICE')

        self.add_argument('-i', '--interface', dest='can_interface',
                          help="SocketCAN interface, e.g 'can0' (Linux only).",
                          metavar='INTERFACE')


    def parse_args(self, *args, **kwargs):
        args = super(ConnectionArgumentParser, self).parse_args(*args, **kwargs)

        if args.serial_device is None and \
           args.can_interface is None:
            self.error("You must specify one of --tcp, --port or --interface")

        if args.can_interface and args.serial_device:
            self.error("Can only use one of --interface and --port")

        return args

class SocketSerialAdapter:
    """
    This class wraps a socket in an API compatible with PySerial's one.
    """
    def __init__(self, socket):
        self.socket = socket

    def read(self, n):
        try:
            return self.socket.recv(n)
        except socket.timeout:
            return bytes()


    def write(self, data):
        return self.socket.send(data)

    def flush(self):
        pass


def open_connection(args):
    """
    Open a connection based on commandline arguments.

    Returns a file like object which will be the connection handle.
    """
    if args.can_interface:
        return can.adapters.SocketCANConnection(args.can_interface)
    elif args.serial_device:
        port = serial.Serial(port=args.serial_device,
                             timeout=2.0, baudrate=115200)
        return can.adapters.CVRACANDongleConnection(port)

def read_can_datagrams(fdesc):
    buf = defaultdict(lambda: bytes())
    while True:
        datagram = None
        while datagram is None:
            frame = fdesc.receive_frame()

            if frame is None:
                yield None
                continue

            if frame.extended:
                continue

            src = frame.id & (0x7f)
            buf[src] += frame.data

            datagram = can.decode_datagram(buf[src])

            if datagram is not None:
                del buf[src]
                data, dst = datagram

        yield data, dst, src


def ping_board(fdesc, destination):
    """
    Checks if a board is up.

    Returns True if it is online, false otherwise.
    """
    write_command(fdesc, commands.encode_ping(), [destination])

    reader = read_can_datagrams(fdesc)
    answer = next(reader)

    # Timeout
    if answer is None:
        return False

    return True


def write_command(fdesc, command, destinations, source=0):
    """
    Writes the given encoded command to the CAN bridge.
    """
    datagram = can.encode_datagram(command, destinations)
    frames = can.datagram_to_frames(datagram, source)

    for frame in frames:
        fdesc.send_frame(frame)

    time.sleep(0.1)


def write_command_retry(fdesc, command, destinations, source=0, retry_limit=3):
    """
    Writes a command, retries as long as there is no answer and returns a dictionnary containing
    a map of each board ID and its answer.
    """
    write_command(fdesc, command, destinations, source)
    reader = read_can_datagrams(fdesc)
    answers = dict()

    retry_count = 0

    while len(answers) < len(destinations):
        dt = next(reader)

        # If we have a timeout, retry on some boards
        if dt is None:
            if retry_count == retry_limit:
                logging.critical("No answer, aborting...")
                raise IOError

            timedout_boards = list(set(destinations) - set(answers))
            write_command(fdesc, command, timedout_boards, source)
            msg = "The following boards did not answer: {}, retrying..".format(
                " ".join(str(t) for t in timedout_boards))

            logging.warning(msg)
            retry_count += 1

            continue

        data, _, src = dt
        answers[src] = data

    return answers


def config_update_and_save(fdesc, config, destinations):
    """
    Updates the config of the given destinations.
    Keys not in the given config are left unchanged.
    """
    # First send the updated config
    command = commands.encode_update_config(config)
    write_command_retry(fdesc, command, destinations)

    # Then save the config to flash
    write_command_retry(fdesc, commands.encode_save_config(), destinations)
