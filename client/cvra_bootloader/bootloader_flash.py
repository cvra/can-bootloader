#!/usr/bin/env python3
"""
Update firmware using CVRA bootloading protocol.
"""
import logging
from cvra_bootloader import page, commands, utils
import msgpack
from zlib import crc32
from sys import exit

import progressbar
import sys

CHUNK_SIZE = 2048


def parse_commandline_args(args=None):
    """
    Parses the program commandline arguments.
    Args must be an array containing all arguments.
    """
    parser = utils.ConnectionArgumentParser(description=__doc__)
    parser.add_argument('-b', '--binary', dest='binary_file',
                        help='Path to the binary file to upload',
                        required=True,
                        metavar='FILE')

    parser.add_argument('-a', '--base-address', dest='base_address',
                        help='Base address of the firmware',
                        metavar='ADDRESS',
                        required=True,
                        # automatically convert value to hex
                        type=lambda s: int(s, 16))

    parser.add_argument('-c', '--device-class',
                        dest='device_class',
                        help='Device class to flash', required=True)
    parser.add_argument('-r', '--run',
                        help='Run application after flashing',
                        action='store_true')
    parser.add_argument("ids",
                        metavar='DEVICEID',
                        nargs='+', type=int,
                        help="Device IDs to flash")

    return parser.parse_args(args)


def flash_binary(fdesc, binary, base_address, device_class, destinations,
                 page_size=2048):
    """
    Writes a full binary to the flash using the given file descriptor.

    It also takes the binary image, the base address and the device class as
    parameters.
    """

    print("Erasing pages...")
    pbar = progressbar.ProgressBar(maxval=len(binary)).start()

    # First erase all pages
    for offset in range(0, len(binary), page_size):
        erase_command = commands.encode_erase_flash_page(base_address + offset,
                                                         device_class)
        res = utils.write_command_retry(fdesc, erase_command, destinations)

        failed_boards = [str(id) for id, success in res.items()
                         if not msgpack.unpackb(success)]

        if failed_boards:
            msg = ", ".join(failed_boards)
            msg = "Boards {} failed during page erase, aborting...".format(msg)
            logging.critical(msg)
            sys.exit(2)

        pbar.update(offset)

    pbar.finish()

    print("Writing pages...")
    pbar = progressbar.ProgressBar(maxval=len(binary)).start()

    # Then write all pages in chunks
    for offset, chunk in enumerate(page.slice_into_pages(binary, CHUNK_SIZE)):
        offset *= CHUNK_SIZE
        command = commands.encode_write_flash(chunk,
                                              base_address + offset,
                                              device_class)

        res = utils.write_command_retry(fdesc, command, destinations)
        failed_boards = [str(id) for id, success in res.items()
                         if not msgpack.unpackb(success)]

        if failed_boards:
            msg = ", ".join(failed_boards)
            msg = "Boards {} failed during page write, aborting...".format(msg)
            logging.critical(msg)
            sys.exit(2)

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

    expected_crc = crc32(binary)

    command = commands.encode_crc_region(base_address, len(binary))
    utils.write_command(fdesc, command, destinations)

    reader = utils.read_can_datagrams(fdesc)

    boards_checked = 0

    while boards_checked < len(destinations):
        dt = next(reader)

        if dt is None:
            continue

        answer, _, src = dt

        crc = msgpack.unpackb(answer)

        if crc == expected_crc:
            valid_nodes.append(src)

        boards_checked += 1

    return valid_nodes


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
    error_msg = "Verification failed for nodes {}" \
                .format(", ".join(str(x) for x in failed_nodes))
    print(error_msg)
    exit(1)


def check_online_boards(fdesc, boards):
    """
    Returns a set containing the online boards.
    """
    online_boards = set()

    utils.write_command(fdesc, commands.encode_ping(), boards)
    reader = utils.read_can_datagrams(fdesc)

    for dt in reader:
        if dt is None:
            break
        _, _, src = dt
        online_boards.add(src)

    return online_boards


def main():
    """
    Entry point of the application.
    """
    args = parse_commandline_args()
    with open(args.binary_file, 'rb') as input_file:
        binary = input_file.read()

    serial_port = utils.open_connection(args)

    online_boards = check_online_boards(serial_port, args.ids)

    if online_boards != set(args.ids):
        offline_boards = [str(i) for i in set(args.ids) - online_boards]
        print("Boards {} are offline, aborting..."
              .format(", ".join(offline_boards)))
        exit(2)

    print("Flashing firmware (size: {} bytes)".format(len(binary)))
    flash_binary(serial_port, binary, args.base_address, args.device_class,
                 args.ids)

    print("Verifying firmware...")
    valid_nodes_set = set(check_binary(serial_port, binary,
                                       args.base_address, args.ids))
    nodes_set = set(args.ids)

    if valid_nodes_set == nodes_set:
        print("OK")
    else:
        verification_failed(nodes_set - valid_nodes_set)

    if args.run:
        run_application(serial_port, args.ids)


if __name__ == "__main__":
    main()
