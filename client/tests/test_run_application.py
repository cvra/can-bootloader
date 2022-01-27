from unittest import TestCase

try:
    from unittest.mock import *
except ImportError:
    from mock import *

import sys

from cvra_bootloader.run_application import main

from cvra_bootloader import commands


class BootloaderRunApplicationTestCase(TestCase):
    @patch("cvra_bootloader.utils.write_command")
    @patch("cvra_bootloader.utils.open_connection")
    def test_integration(self, open_connection, write_command):
        sys.argv = "test.py -p /dev/ttyUSB0 1 2".split()
        open_connection.return_value = object()

        main()

        command = commands.encode_jump_to_main()
        write_command.assert_any_call(open_connection.return_value, command, [1, 2])
