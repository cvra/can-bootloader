#!/usr/bin/env python3
from cvra_bootloader import commands, utils

def parse_commandline_args():
    parser = utils.ConnectionArgumentParser(description='Send a jump to application command.')
    parser.add_argument("ids", metavar='DEVICEID', nargs='*', type=int,
                        help="Device IDs to send jump command")
    parser.add_argument('-a', '--all', help="Try to scan all network.",
                        action='store_true')

    return parser.parse_args()

def main():
    args = parse_commandline_args()
    connection = utils.open_connection(args)
    if args.all is True:
        ids = list(range(1, 128))
    else:
        ids = args.ids

    utils.write_command(connection, commands.encode_jump_to_main(), ids)

if __name__ == "__main__":
    main()
