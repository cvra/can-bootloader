#!/usr/bin/env python3
from cvra_bootloader import commands, utils
import msgpack
import json


def parse_commandline_args():
    """
    Parses the program commandline arguments.
    """
    DESCRIPTION = 'Read board configs and dumps to JSON'
    parser = utils.ConnectionArgumentParser(description=DESCRIPTION)
    parser.add_argument("ids", metavar='DEVICEID', nargs='*', type=int,
                        help="Device IDs to flash")

    parser.add_argument('-a', '--all', help="Try to scan all network.",
                        action='store_true')

    return parser.parse_args()


def main():
    args = parse_commandline_args()
    connection = utils.open_connection(args)

    if args.all:
        scan_queue = list()

        # Broadcast ping
        utils.write_command(connection, commands.encode_ping(), list(range(1, 128)))
        reader = utils.read_can_datagrams(connection)
        while True:
            dt = next(reader)

            if dt is None: # Timeout
                break

            _, _, src = dt
            scan_queue.append(src)

    else:
        scan_queue = args.ids

    # Broadcast ask for config
    configs = utils.write_command_retry(connection,
                                        commands.encode_read_config(),
                                        scan_queue)

    for id, raw_config in configs.items():
        configs[id] = msgpack.unpackb(raw_config, encoding='ascii')

    print(json.dumps(configs, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()
