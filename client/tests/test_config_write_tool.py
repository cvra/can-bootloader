import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

from cvra_bootloader.write_config import main
from io import StringIO
import sys


class WriteConfigToolTestCase(unittest.TestCase):
    @patch("cvra_bootloader.utils.config_update_and_save")
    @patch("cvra_bootloader.utils.open_connection")
    @patch("builtins.open")
    def test_integration(self, open_mock, open_conn, config_save):
        sys.argv = "test.py -c test.json -p /dev/ttyUSB0 1 2 3".split()
        config_file = '{"foo":12}'

        open_mock.return_value = StringIO(config_file)
        open_conn.return_value = object()

        main()

        open_mock.assert_any_call("test.json")
        config_save.assert_any_call(open_conn.return_value, {"foo": 12}, [1, 2, 3])

    @patch("builtins.open")
    @patch("builtins.print")
    def test_fails_on_ID_change(self, print_mock, open_mock):
        """
        Checks that this tool refuses to change a Node ID.
        """
        sys.argv = "test.py -c nonexisting.json -p /dev/ttyUSB0 1 2 3".split()
        config_file = '{"ID":11}'

        open_mock.return_value = StringIO(config_file)

        with self.assertRaises(SystemExit):
            main()
