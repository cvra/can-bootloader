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



@patch('utils.CANDatagramReader.read_datagram')
@patch('utils.write_command')
class CommandRetryTestCase(unittest.TestCase):
    def test_write_is_forwarded(self, write, read):
        port = object()
        read.return_value = (bytes(), [10], 1)

        write_command_retry(port, bytes([1, 2, 3]), [1], source=10)
        write.assert_any_call(port, bytes([1, 2, 3]), [1], 10)

    def test_return_dict(self, write, read):
        read.side_effect = [(20, [10], 2), (10, [10], 1)]
        res = write_command_retry(None, None, [1, 2])
        self.assertEqual(res, {1: 10, 2: 20})

    def test_retry(self, write, read):
        data = "hello"
        read.side_effect = [(20, [10], 2), None, (10, [10], 1)]

        with patch('logging.warning') as w:
            res = write_command_retry(None, data, [1, 2])
            w.assert_any_call(ANY)

        # Check that we retrued for the board who timed out
        write.assert_any_call(None, data, [1, 2], 0)
        write.assert_any_call(None, data, [1], 0)

        self.assertEqual(res, {1: 10, 2: 20})
