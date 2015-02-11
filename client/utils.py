import serial
import socket

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
        return connection.makefile('w+b')

def write_command(fdesc, command, destinations, source=0):
    """
    Writes the given encoded command to the CAN bridge.
    """
    datagram = can.encode_datagram(command, destinations)
    frames = can.datagram_to_frames(datagram, source)
    for frame in frames:
        bridge_frame = can_bridge.encode_frame_command(frame)
        datagram = serial_datagrams.datagram_encode(bridge_frame)
        fdesc.write(datagram)
    time.sleep(0.3)
