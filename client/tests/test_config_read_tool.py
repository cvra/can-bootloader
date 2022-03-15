import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

from msgpack import *

from cvra_bootloader.read_config import main
from cvra_bootloader.commands import *
import sys
import json


class ReadConfigToolTestCase(unittest.TestCase):
    @patch("cvra_bootloader.utils.write_command_retry")
    @patch("cvra_bootloader.utils.write_command")
    @patch("cvra_bootloader.utils.open_connection")
    @patch("builtins.print")
    def test_integration(
        self, print_mock, open_conn, write_command, write_command_retry
    ):
        sys.argv = "test.py -p /dev/ttyUSB0 0 1 2".split()
        configs = [{"id": i} for i in range(3)]

        write_command_retry.return_value = {i: packb(configs[i]) for i in range(3)}

        open_conn.return_value = object()

        main()

        write_command_retry.assert_any_call(
            open_conn.return_value, encode_read_config(), [0, 1, 2]
        )

        all_configs = {i: configs[i] for i in range(3)}

        print_mock.assert_any_call(json.dumps(all_configs, indent=4, sort_keys=True))

    @patch("cvra_bootloader.utils.open_connection")
    @patch("cvra_bootloader.utils.write_command_retry")
    @patch("cvra_bootloader.utils.write_command")
    @patch("cvra_bootloader.utils.read_can_datagrams")
    @patch("builtins.print")
    def test_network_discovery(
        self,
        print_mock,
        read_can_datagram,
        write_command,
        write_command_retry,
        open_conn,
    ):
        """
        Checks if we can perform a whole network discovery.
        """
        sys.argv = "test.py -p /dev/ttyUSB0 --all".split()

        # The first two board answers the ping
        board_answers = [(b"", [0], i) for i in range(1, 3)] + [None]

        read_can_datagram.return_value = iter(board_answers)

        write_command_retry.return_value = {i: packb({"id": i}) for i in range(1, 3)}

        main()
        write_command.assert_any_call(
            open_conn.return_value, encode_ping(), list(range(1, 128))
        )
