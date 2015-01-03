import argparse
import page
import commands
import serial_datagrams, can, can_bridge
import msgpack
from zlib import crc32

CHUNK_SIZE = 2048

def parse_commandline_args(args=None):
    """
    Parses the program commandline arguments.
    Args must be an array containing all arguments.
    """
    parser = argparse.ArgumentParser(description='Update firmware using CVRA bootloading protocol.')
    parser.add_argument('-b', '--binary', dest='binary_file',
                        help='Path to the binary file to upload',
                        required=True,
                        metavar='FILE')

    parser.add_argument('-a', '--base-adress', dest='base_adress',
                        help='Base adress of the firmware (binary files only)',
                        metavar='ADRESS',
                        required=True,
                        type=lambda s: int(s, 16)) # automatically convert value to hex

    parser.add_argument('-p', '--port', dest='serial_device',
                        required=True,
                        help='Serial port to which the CAN port is connected to.',
                        metavar='DEVICE')

    parser.add_argument('device_class', help='Device class to flash')
    parser.add_argument("id", nargs='+', type=int, help="Device IDs to flash")

    return parser.parse_args(args)

def write_command(fdesc, command, destinations, source=0):
    """
    Writes the given encoded command to the CAN bridge.
    """
    datagram = can.encode_datagram(command, destinations)
    frames = can.datagram_to_frames(datagram, source)
    for f in frames:
        bridge_frame = can_bridge.encode_frame_command(frame)
        datagram = serial_datagrams.datagram_encode(bridge_frame)
        fdesc.write(datagram)

def flash_binary(fdesc, binary, base_adress, device_class, destinations, page_size=2048):
    """
    Writes a full binary to the flash using the given file descriptor.

    It also takes the binary image, the base adress and the device class as
    parameters.
    """

    # First erase all pagesj
    for offset in range(0, len(binary), page_size):
        erase_command = commands.encode_erase_flash_page(base_adress + offset, device_class)
        write_command(fdesc, erase_command, destinations)

    # Then write all pages in chunks
    for offset, chunk in enumerate(page.slice_into_pages(binary, CHUNK_SIZE)):
        offset *= CHUNK_SIZE
        command = commands.encode_write_flash(chunk, base_adress + offset, device_class)
        write_command(fdesc, command, destinations)

    # Finally update application CRC and size in config
    config = dict()
    config['application_size'] = len(binary)
    config['application_crc'] = crc32(binary)
    config_update_and_save(fdesc, config, destinations)

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

def read_can_datagram(fdesc):
    """
    Reads a full CAN datagram from the CAN <-> serial bridge.
    """
    buf = bytes()
    dt = None

    while dt is None:
        frame = serial_datagrams.read_datagram(fdesc)
        frame = can_bridge.decode_frame(frame)
        buf += frame.data
        dt = can.decode_datagram(buf)

    return dt

def crc_region(fdesc, base_address, length, destination):
    """
    Asks a single board for the CRC of a region.
    """
    command = commands.encode_crc_region(base_address, length)
    write_command(fdesc, command, [destination])
    answer = read_can_datagram(fdesc)

    return msgpack.unpackb(answer)



if __name__ == "__main__":
    parse_commandline_args()
    fd = serial.Serial(args.serialdev, baudrate=args.baud, timeout=0.2)

