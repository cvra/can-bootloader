#!/usr/bin/env python3
import utils

import can
import can_bridge
import serial_datagrams

def read_frame(fdesc):
    """
    Reads a full CAN datagram from the CAN <-> serial bridge.
    """
    buf = bytes()
    datagram = None

    frame = serial_datagrams.read_datagram(fdesc)
    frame = can_bridge.decode_frame(frame)

    return frame

def send_frame(fdesc, frame):
    bridge_frame = can_bridge.encode_frame_command(frame)
    datagram = serial_datagrams.datagram_encode(bridge_frame)
    fdesc.write(datagram)
    fdesc.flush()

def main():
    DATA = "CVRA"

    parser = utils.ConnectionArgumentParser(description='Tests the CAN loopback over the Brige')
    args = parser.parse_args()

    connection = utils.open_connection(args)

    frame = can.Frame(data=DATA.encode())
    send_frame(connection, frame)
    print("Sent {}".format(DATA))

    answer = read_frame(connection)

    print("Got {}".format(answer.data.decode()))



if __name__ == "__main__":
    main()
