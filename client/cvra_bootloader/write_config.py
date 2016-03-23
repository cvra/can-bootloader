#!/usr/bin/env python3

import sys
import json

from cvra_bootloader import utils

def parse_commandline_args():
    """
    Parses the program commandline arguments.
    Args must be an array containing all arguments.
    """

    epilog = '''
    The configuration file must contained a JSON-encoded map. Example: "{"name":"foo"}".
    '''

    parser = utils.ConnectionArgumentParser(description='Update config (key/value pairs) on a board', epilog=epilog)
    parser.add_argument("-c", "--config", help="JSON file to load config from (default stdin)", type=open, default=sys.stdin, dest='file')
    parser.add_argument("ids", metavar='DEVICEID', nargs='+', type=int, help="Device IDs to flash")


    return parser.parse_args()


def main():
    args = parse_commandline_args()
    config = json.loads(args.file.read())

    if "ID" in config.keys():
        print("This tool cannot be used to change node IDs.")
        print("Use bootloader_change_id.py instead.")
        sys.exit(1)

    connection = utils.open_connection(args)
    utils.config_update_and_save(connection, config, args.ids)

if __name__ == "__main__":
    main()
