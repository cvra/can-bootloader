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
    @patch('serial.Serial')
    def test_integration(self, serial, write_command):
        sys.argv = "test.py -p /dev/ttyUSB0 1 2".split()
        serial.return_value = object()

        bootloader_change_id.main()
        serial.assert_any_call(port='/dev/ttyUSB0', timeout=ANY, baudrate=ANY)

        command = commands.encode_update_config({'ID': 2})
        write_command.assert_any_call(serial.return_value, command, [1])

        command = commands.encode_save_config()
        write_command.assert_any_call(serial.return_value, command, [2])
