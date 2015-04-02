import unittest
try:
    from unittest.mock import *
except ImportError:
    from mock import *

from utils import *

import commands
import msgpack
import can_bridge.commands
import serial_datagrams
import io

@patch('utils.CANDatagramReader.read_datagram')
@patch('utils.write_command')
class BoardPingTestCase(unittest.TestCase):
    """
    Checks for the ping_board function.
    """
    def test_sends_correct_command(self, write_command, read_datagram):
        port = object()
        ping_board(port, 1)

        write_command.assert_any_call(port, commands.encode_ping(), [1])
        read_datagram.assert_any_call()

    def test_answers_false_if_no_answer(self, write_command, read_datagram):
        read_datagram.return_value = None # timeout

        port = object()
        self.assertFalse(ping_board(port, 1))

    def test_answers_true_if_pong(self, write_command, read_datagram):
        read_datagram.return_value = msgpack.packb(True), [0]

        port = object()
        self.assertTrue(ping_board(port, 1))


class BridgeConfigTestCase(unittest.TestCase):
    def test_configures_bridge(self):
        expected_data = can_bridge.commands.encode_id_filter_set(
            extended_frame=False)
        expected_data = serial_datagrams.datagram_encode(expected_data)

        port = io.BytesIO()
        setup_bridge(port)
        self.assertEqual(port.getvalue(), expected_data)
