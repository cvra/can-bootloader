import argparse
import page
import commands

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

if __name__ == "__main__":
    parse_commandline_args()
    fd = serial.Serial(args.serialdev, baudrate=args.baud, timeout=0.2)

