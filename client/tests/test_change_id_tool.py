import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

import sys
import bootloader_change_id
import commands


class BootloaderChangeIdTestCase(unittest.TestCase):
    @patch('utils.write_command_retry')
    @patch('utils.open_connection')
    def test_integration(self, open_connection, write_command):
        sys.argv = "test.py -p /dev/ttyUSB0 1 2".split()
        open_connection.return_value = object()

        bootloader_change_id.main()

        command = commands.encode_update_config({'ID': 2})
        write_command.assert_any_call(open_connection.return_value, command, [1])

        command = commands.encode_save_config()
        write_command.assert_any_call(open_connection.return_value, command, [2])
