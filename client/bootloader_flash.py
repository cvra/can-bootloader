#!/usr/bin/env python
import argparse
import page
import commands
import serial_datagrams, can, can_bridge
import msgpack
from zlib import crc32
from sys import exit
import time

import utils
import progressbar

CHUNK_SIZE = 2048

def parse_commandline_args(args=None):
    """
    Parses the program commandline arguments.
    Args must be an array containing all arguments.
    """
    parser = utils.ConnectionArgumentParser(description='Update firmware using CVRA bootloading protocol.')
    parser.add_argument('-b', '--binary', dest='binary_file',
                        help='Path to the binary file to upload',
                        required=True,
                        metavar='FILE')

    parser.add_argument('-a', '--base-address', dest='base_address',
                        help='Base address of the firmware (binary files only)',
                        metavar='ADDRESS',
                        required=True,
                        type=lambda s: int(s, 16)) # automatically convert value to hex


    parser.add_argument('-c', '--device-class', dest='device_class', help='Device class to flash', required=True)
    parser.add_argument('-r', '--run', help='Run application after flashing', action='store_true')
    parser.add_argument("ids", metavar='DEVICEID', nargs='+', type=int, help="Device IDs to flash")


    args = parser.parse_args(args)


    return args

def flash_binary(fdesc, binary, base_address, device_class, destinations, page_size=2048):
    """
    Writes a full binary to the flash using the given file descriptor.

    It also takes the binary image, the base address and the device class as
    parameters.
    """

    print("Erasing pages...")
    pbar = progressbar.ProgressBar(maxval=len(binary)).start()

    # First erase all pages
    for offset in range(0, len(binary), page_size):
        erase_command = commands.encode_erase_flash_page(base_address + offset, device_class)
        utils.write_command(fdesc, erase_command, destinations)
        pbar.update(offset)

    pbar.finish()

    print("Writing pages...")
    pbar = progressbar.ProgressBar(maxval=len(binary)).start()

    # Then write all pages in chunks
    for offset, chunk in enumerate(page.slice_into_pages(binary, CHUNK_SIZE)):
        offset *= CHUNK_SIZE
        command = commands.encode_write_flash(chunk, base_address + offset, device_class)
        utils.write_command(fdesc, command, destinations)
        pbar.update(offset)
    pbar.finish()

    # Finally update application CRC and size in config
    config = dict()
    config['application_size'] = len(binary)
    config['application_crc'] = crc32(binary)
    utils.config_update_and_save(fdesc, config, destinations)

def check_binary(fdesc, binary, base_address, destinations):
    """
    Check that the binary was correctly written to all destinations.

    Returns a list of all nodes which are passing the test.
    """
    valid_nodes = []
    for node in destinations:
        crc = crc_region(fdesc, base_address, len(binary), node)
        if crc == crc32(binary):
            valid_nodes.append(node)

    return valid_nodes


def read_can_datagram(fdesc):
    """
    Reads a full CAN datagram from the CAN <-> serial bridge.
    """
    buf = bytes()
    datagram = None

    while datagram is None:
        frame = serial_datagrams.read_datagram(fdesc)
        if frame is None: # Timeout, retry
            continue
        frame = can_bridge.decode_frame(frame)
        buf += frame.data
        datagram = can.decode_datagram(buf)

    return datagram

def crc_region(fdesc, base_address, length, destination):
    """
    Asks a single board for the CRC of a region.
    """
    command = commands.encode_crc_region(base_address, length)
    utils.write_command(fdesc, command, [destination])
    answer, _ = read_can_datagram(fdesc)

    return msgpack.unpackb(answer)

def run_application(fdesc, destinations):
    """
    Asks the given node to run the application.
    """
    command = commands.encode_jump_to_main()
    utils.write_command(fdesc, command, destinations)

def verification_failed(failed_nodes):
    """
    Prints a message about the verification failing and exits
    """
    error_msg = "Verification failed for nodes {}".format(", ".join(str(x) for x in failed_nodes))
    print(error_msg)
    exit(1)


def main():
    """
    Entry point of the application.
    """
    args = parse_commandline_args()
    with open(args.binary_file, 'rb') as input_file:
        binary = input_file.read()

    serial_port = utils.open_connection(args)

    print("Flashing firmware (size: {} bytes)".format(len(binary)))
    flash_binary(serial_port, binary, args.base_address, args.device_class, args.ids)

    print("Verifying firmware...")
    valid_nodes_set = set(check_binary(serial_port, binary, args.base_address, args.ids))
    nodes_set = set(args.ids)

    if valid_nodes_set == nodes_set:
        print("OK")
    else:
        verification_failed(nodes_set - valid_nodes_set)

    if args.run:
        run_application(serial_port, args.ids)



if __name__ == "__main__":
    main()

