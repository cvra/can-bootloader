#!/usr/bin/env python

import sys
import json

import utils

def parse_commandline_args():
    """
    Parses the program commandline arguments.
    Args must be an array containing all arguments.
    """
    parser = utils.ConnectionArgumentParser(description='Update config (key/value pairs) on a board')
    parser.add_argument("-c", "--config", help="JSON file to load config from (default stdin)", type=open, default=sys.stdin, dest='file')
    parser.add_argument("ids", metavar='DEVICEID', nargs='+', type=int, help="Device IDs to flash")


    return parser.parse_args()


def main():
    args = parse_commandline_args()
    connection = utils.open_connection(args)
    config = json.loads(args.file.read().decode())
    utils.config_update_and_save(connection, config, args.ids)

if __name__ == "__main__":
    main()
