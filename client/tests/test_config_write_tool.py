import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

import bootloader_write_config
from io import StringIO
import sys

class WriteConfigToolTestCase(unittest.TestCase):
    @patch('utils.config_update_and_save')
    @patch('serial.Serial')
    @patch('builtins.open')
    def test_integration(self, open_mock, serial, config_save):
        sys.argv = "test.py -c test.json -p /dev/ttyUSB0 1 2 3".split()
        config_file = '{"foo":12}'

        open_mock.return_value = StringIO(config_file)
        serial.return_value = object()

        bootloader_write_config.main()

        open_mock.assert_any_call('test.json')
        serial.assert_any_call(port='/dev/ttyUSB0', timeout=ANY, baudrate=ANY)
        config_save.assert_any_call(serial.return_value, {'foo':12}, [1, 2, 3])







