import unittest
try:
    from unittest.mock import *
except ImportError:
    from mock import *

from utils import *

import commands
import msgpack

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


