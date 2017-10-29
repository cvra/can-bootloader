import unittest
try:
    from unittest.mock import *
except ImportError:
    from mock import *

from cvra_bootloader.utils import *
from itertools import repeat
from collections import namedtuple

from cvra_bootloader import commands
import msgpack
import io

@patch('cvra_bootloader.utils.read_can_datagrams')
@patch('cvra_bootloader.utils.write_command')
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
        frames = list(can.datagram_to_frames(datagram, 0))

        fdesc = Mock()

        # Writes CAN frame
        write_command(fdesc, data, dst)

        # Asserts writes are OK
        for f in frames:
            fdesc.send_frame.assert_any_call(f)



@patch('cvra_bootloader.utils.read_can_datagrams')
@patch('cvra_bootloader.utils.write_command')
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

class PCAPWrapperTestCase(unittest.TestCase):
    def setUp(self):
        self.underlying_conn = Mock()
        self.outfile = io.BytesIO()
        self.conn = PcapConnectionWrapper(self.underlying_conn, self.outfile)

    def test_write_header(self):
        """
        Check that a pcap file header was written
        """
        self.assertEqual(24, len(self.outfile.getvalue()))

    def test_write_frame(self):
        """
        Checks that a pcap frame was logged and the frame was forwarded.
        """
        f = can.Frame(0, "hello".encode())
        self.conn.send_frame(f)

        # The frame should have been sent and logged to the file
        self.assertEqual(53, len(self.outfile.getvalue()), 'no data in pcap')
        self.underlying_conn.send_frame.assert_any_call(f)

    def test_receive_frame(self):
        """
        Checks that we can still receive frame and log them to the disk.
        """
        f = can.Frame(0, "hello".encode())
        self.underlying_conn.receive_frame.return_value = f

        self.assertEqual(f, self.conn.receive_frame())
        self.assertEqual(53, len(self.outfile.getvalue()), 'no data in pcap')

    def test_receive_frame_timeout(self):
        """
        Checks that read timeoutes are not logged in the pcap.
        """
        self.underlying_conn.receive_frame.return_value = None # timeout
        self.assertIsNone(self.conn.receive_frame())
        self.assertEqual(24, len(self.outfile.getvalue()), 'pcap should only contain header')

class OpenConnectionTestCase(unittest.TestCase):
    Args = namedtuple("Args", ["serial_device", "can_interface", "pcap"])

    def make_args(self, serial_device=None, can_interface=None, pcap=None):
        return self.Args(serial_device=serial_device, can_interface=can_interface, pcap=pcap)

    @patch('can.adapters.SocketCANConnection', autospec=True)
    def test_open_can_interface(self, create_socket):
        """
        Check that we can open a socket CAN adapter.
        """
        args = self.make_args(can_interface='can0')
        conn = open_connection(args)
        create_socket.assert_any_call('can0')
        self.assertEqual(conn, create_socket.return_value)

    @patch('can.adapters.SocketCANConnection', autospec=True)
    def test_pcap_wrapper(self, create_socket):
        """
        Check that we can open a socket CAN adapter.
        """
        outfile = io.BytesIO()
        args = self.make_args(can_interface='can0', pcap=outfile)
        conn = open_connection(args)
        create_socket.assert_any_call('can0')
        self.assertEqual(conn.conn, create_socket.return_value)


class ArgumentParserTestCase(unittest.TestCase):
    def test_socketcan(self):
        parser = ConnectionArgumentParser()
        args = parser.parse_args("-i can0".split())

        self.assertEqual('can0', args.can_interface)

