import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

from msgpack import *

import bootloader_read_config
from commands import *
import sys
import json

class ReadConfigToolTestCase(unittest.TestCase):
    @patch('utils.CANDatagramReader.read_datagram')
    @patch('utils.write_command')
    @patch('serial.Serial')
    @patch('builtins.print')
    def test_integration(self, print_mock, serial, write_command, read_can_datagram):
        sys.argv = "test.py -p /dev/ttyUSB0 0 1 2".split()
        configs = [{'id':i} for i in range(3)]

        read_can_datagram.side_effect = [(packb(c), 0, 0) for c in configs]

        serial.return_value = object()

        bootloader_read_config.main()

        serial.assert_any_call(port='/dev/ttyUSB0', timeout=ANY, baudrate=ANY)

        for i in range(3):
            write_command.assert_any_call(serial.return_value, encode_read_config(), [i])
            read_can_datagram.assert_any_call()

        all_configs = {i:configs[i] for i in range(3)}

        print_mock.assert_any_call(json.dumps(all_configs, indent=4, sort_keys=True))
