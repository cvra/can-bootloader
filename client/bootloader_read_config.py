#!/usr/bin/env python
import utils
import commands
import msgpack
import json


def parse_commandline_args():
    """
    Parses the program commandline arguments.
    """
    DESCRIPTION = 'Read board configs and dumps to JSON'
    parser = utils.ConnectionArgumentParser(description=DESCRIPTION)
    parser.add_argument("ids", metavar='DEVICEID', nargs='+', type=int,
                        help="Device IDs to flash")

    return parser.parse_args()


def main():
    args = parse_commandline_args()
    connection = utils.open_connection(args)

    configs = dict()

    reader = utils.CANDatagramReader(connection)

    # Broadcast ask for config
    utils.write_command(connection, commands.encode_read_config(), args.ids)

    for id in args.ids:
        answer, _, src = reader.read_datagram()
        configs[src] = msgpack.unpackb(answer, encoding='ascii')

    print(json.dumps(configs, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()
