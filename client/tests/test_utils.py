import unittest
try:
    from unittest.mock import *
except ImportError:
    from mock import *

from utils import *
from itertools import repeat
from collections import namedtuple
from can.adapters import SerialCANBridgeConnection

import commands
import msgpack
import serial_datagrams
import can_bridge

@patch('utils.read_can_datagrams')
@patch('utils.write_command')
class BoardPingTestCase(unittest.TestCase):
    """
    Checks for the ping_board function.
    """
    def test_sends_correct_command(self, write_command, read_datagram):
        port = object()
        ping_board(port, 1)

        write_command.assert_any_call(port, commands.encode_ping(), [1])

    def test_answers_false_if_no_answer(self, write_command, read_datagram):
        read_datagram.return_value = iter([None])  # timeout

        port = object()
        self.assertFalse(ping_board(port, 1))

    def test_answers_true_if_pong(self, write_command, read_datagram):
        read_datagram.return_value = iter([(msgpack.packb(True), [0])])

        port = object()
        self.assertTrue(ping_board(port, 1))


@patch('time.sleep')
class WriteCommandTestCase(unittest.TestCase):
    def test_write(self, sleep):
        # Prepares data
        data = bytes(range(3))
        dst = [1, 2]
        datagram = can.encode_datagram(data, dst)
        frames = can.datagram_to_frames(datagram, 0)

        bridge_frames = [can_bridge.commands.encode_frame_write(f)
                         for f in frames]

        bridge_datagrams = [serial_datagrams.datagram_encode(f)
                            for f in bridge_frames]

        fdesc = Mock()
        conn = SerialCANBridgeConnection(fdesc)

        # Writes CAN frame
        write_command(conn, data, dst)

        # Asserts writes are OK
        for dt in bridge_datagrams:
            fdesc.write.assert_any_call(dt)
            fdesc.flush.assert_any_call()



@patch('utils.read_can_datagrams')
@patch('utils.write_command')
class CommandRetryTestCase(unittest.TestCase):
    def test_write_is_forwarded(self, write, read):
        port = object()
        read.return_value = iter([(bytes(), [10], 1)])

        write_command_retry(port, bytes([1, 2, 3]), [1], source=10)
        write.assert_any_call(port, bytes([1, 2, 3]), [1], 10)

    def test_return_dict(self, write, read):
        read.return_value = iter([(20, [10], 2), (10, [10], 1)])
        res = write_command_retry(None, None, [1, 2])
        self.assertEqual(res, {1: 10, 2: 20})

    def test_retry(self, write, read):
        data = "hello"
        read.return_value = iter([(20, [10], 2), None, (10, [10], 1)])

        with patch('logging.warning') as w:
            write_command_retry(None, data, [1, 2])
            w.assert_any_call(ANY)

        # Check that we retrued for the board who timed out
        write.assert_any_call(None, data, [1, 2], 0)
        write.assert_any_call(None, data, [1], 0)

    def test_retry_limit(self, write, read):
        """
        Check that the retry limit is enforced.
        """
        read.return_value = repeat(None)  # Timeout forever
        data = "hello"

        with patch('logging.warning'),  patch('logging.critical') as critical:
            with self.assertRaises(IOError):
                write_command_retry(None, data, [1, 2], retry_limit=2)

            # Check that we tried the correct number of time and showed a
            # message
            self.assertEqual(write.call_count, 2 + 1)
            critical.assert_any_call(ANY)


class OpenConnectionTestCase(unittest.TestCase):
    Args = namedtuple("Args", ["hostname", "serial_device"])

    def make_args(self, hostname=None, serial_device=None):
        return self.Args(hostname=hostname, serial_device=serial_device)

    def test_open_serial(self):
        """
        Checks that if we provide a serial port the serial port is
        """
        args = self.make_args(serial_device='/dev/ttyUSB0')

        with patch('serial.Serial') as serial:
            serial.return_value = object()
            port = open_connection(args)

            self.assertEqual(port.fd, serial.return_value)
            serial.assert_any_call(port="/dev/ttyUSB0",
                                   baudrate=ANY, timeout=ANY)

    def test_open_hostname_default_port(self):
        """
        Checks that we can open a connection to a hostname with the default
        port.
        """
        args = self.make_args(hostname="10.0.0.10")

        with patch('socket.create_connection') as create_connection:
            create_connection.return_value = Mock()
            port = open_connection(args)

            create_connection.assert_any_call(('10.0.0.10', 1337))

            self.assertEqual(port.fd.socket,
                             create_connection.return_value)

    def test_open_hostname_custom_port(self):
        """
        Checks if we can open a connection to a hostname on a different port.
        """
        args = self.make_args(hostname="10.0.0.10:42")
        with patch('socket.create_connection') as create_connection:
            open_connection(args)
            create_connection.assert_any_call(('10.0.0.10', 42))
