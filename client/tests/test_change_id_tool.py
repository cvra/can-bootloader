import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

import sys
from cvra_bootloader.change_id import main
import cvra_bootloader.commands


class BootloaderChangeIdTestCase(unittest.TestCase):
    @patch("cvra_bootloader.utils.write_command_retry")
    @patch("cvra_bootloader.utils.open_connection")
    def test_integration(self, open_connection, write_command):
        sys.argv = "test.py -p /dev/ttyUSB0 1 2".split()
        open_connection.return_value = object()

        main()

        command = cvra_bootloader.commands.encode_update_config({"ID": 2})
        write_command.assert_any_call(open_connection.return_value, command, [1])

        command = cvra_bootloader.commands.encode_save_config()
        write_command.assert_any_call(open_connection.return_value, command, [2])
