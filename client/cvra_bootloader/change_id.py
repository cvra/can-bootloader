#!/usr/bin/env python3
from cvra_bootloader import commands, utils


def parse_commandline_args():
    parser = utils.ConnectionArgumentParser(description='Change a single node ID.')
    parser.add_argument("old", type=int, help="Old device ID")
    parser.add_argument("new", type=int, help="New device ID")

    return parser.parse_args()


def main():
    args = parse_commandline_args()
    connection = utils.open_connection(args)

    config = {"ID": args.new}
    utils.write_command_retry(connection,
                              commands.encode_update_config(config),
                              [args.old])
    utils.write_command_retry(connection,
                              commands.encode_save_config(),
                              [args.new])

if __name__ == "__main__":
    main()
