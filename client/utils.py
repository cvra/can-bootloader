import serial
import socket
import argparse
import time

import commands
import can
import can_bridge
import serial_datagrams
from collections import defaultdict

class ConnectionArgumentParser(argparse.ArgumentParser):
    """
    Subclass of ArgumentParser with default arguments for connection handling (TCP and serial).

    It also checks that the user provides at least one connection method (--tcp or --port).
    """

    def __init__(self, *args, **kwargs):
        super(ConnectionArgumentParser, self).__init__(*args, **kwargs)

        self.add_argument('--tcp', dest='hostname', help="Use TCP/IP instead of serial port (host:port format).", metavar="HOST")
        self.add_argument('-p', '--port', dest='serial_device',
                          help='Serial port to which the CAN bridge is connected to.',
                          metavar='DEVICE')

    def parse_args(self, *args, **kwargs):
        args = super(ConnectionArgumentParser, self).parse_args(*args, **kwargs)

        if args.hostname is None and args.serial_device is None:
            self.error("You must specify one of --tcp or --port")

        if args.hostname and args.serial_device:
            self.error("Can only use one of--tcp and --port")

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
    if args.serial_device:
        return serial.Serial(port=args.serial_device, timeout=0.2, baudrate=115200)

    elif args.hostname:
        try:
            host, port = args.hostname.split(":")
        except ValueError:
            host, port = args.hostname, 1337

        port = int(port)

        connection = socket.create_connection((host, port))
        connection.settimeout(0.2)
        return SocketSerialAdapter(connection)

class CANDatagramReader:
    """
    This class implements CAN datagram reading.

    It supports reading interleaved datagrams through internal buffering.
    """
    def __init__(self, fdesc):
        self.fdesc = fdesc
        self.buf = defaultdict(lambda: bytes())

    def read_datagram(self):
        """
        Reads a single datagram.
        """
        datagram = None

        while datagram is None:
            frame = serial_datagrams.read_datagram(self.fdesc)
            if frame is None: # Timeout, retry
                return None

            frame = can_bridge.frame.decode(frame)

            src = frame.id & (0x7f)
            self.buf[src] += frame.data

            datagram = can.decode_datagram(self.buf[src])

            if datagram is not None:
                data, dst = datagram

        return data, dst, src


def ping_board(fdesc, destination):
    """
    Checks if a board is up.

    Returns True if it is online, false otherwise.
    """
    write_command(fdesc, commands.encode_ping(), [destination])

    reader = CANDatagramReader(fdesc)
    answer = reader.read_datagram()

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
        bridge_frame = can_bridge.commands.encode_frame_write(frame)
        datagram = serial_datagrams.datagram_encode(bridge_frame)
        fdesc.write(datagram)
        fdesc.flush()
    time.sleep(0.3)


def config_update_and_save(fdesc, config, destinations):
    """
    Updates the config of the given destinations.
    Keys not in the given config are left unchanged.
    """
    # First send the updated config
    command = commands.encode_update_config(config)
    write_command(fdesc, command, destinations)

    # Then save the config to flash
    write_command(fdesc, commands.encode_save_config(), destinations)

