import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

from serial import Serial
from zlib import crc32

from bootloader_flash import *
from commands import *
from utils import *
from collections import namedtuple
import msgpack

from io import BytesIO

import can, serial_datagrams
import can_bridge.frame
import sys

@patch('utils.write_command_retry')
class FlashBinaryTestCase(unittest.TestCase):
    fd = "port"

    def setUp(self):
        mock = lambda m: patch(m).start()
        self.progressbar = mock('progressbar.ProgressBar')
        self.print = mock('builtins.print')

    def tearDown(self):
        patch.stopall()

    def test_single_page_erase(self, write):
        """
        Checks that a single page is erased before writing.
        """
        data = bytes(range(20))
        address = 0x1000
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, data, address, "dummy", destinations)

        erase_command = encode_erase_flash_page(address, device_class)
        write.assert_any_call(self.fd, erase_command, destinations)

    def test_write_single_chunk(self, write):
        """
        Tests that a single chunk can be written.
        """
        data = bytes(range(20))
        address = 0x1000
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, data, address, "dummy", [1])

        write_command = encode_write_flash(data, address, device_class)

        write.assert_any_call(self.fd, write_command, destinations)

    def test_write_many_chunks(self, write):
        """
        Checks that we can write many chunks, but still in one page
        """
        data = bytes([0] * 4096)
        address = 0x1000
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, data, address, "dummy", [1])

        write_command = encode_write_flash(bytes([0] * 2048), address, device_class)
        write.assert_any_call(self.fd, write_command, destinations)

        write_command = encode_write_flash(bytes([0] * 2048), address + 2048, device_class)
        write.assert_any_call(self.fd, write_command, destinations)

    def test_erase_multiple_pages(self, write):
        """
        Checks that all pages are erased before writing data to them.
        """
        data = bytes([0] * 4096)
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, bytes([0] * 4096), 0x1000, device_class, destinations, page_size=2048)

        # Check that all pages were erased correctly
        for addr in [0x1000, 0x1800]:
            erase_command = encode_erase_flash_page(addr, device_class)
            write.assert_any_call(self.fd, erase_command, destinations)

    @patch('utils.config_update_and_save')
    def test_crc_is_updated(self, conf, write):
        """
        Tests that the CRC is updated after flashing a binary.
        """
        data = bytes([0] * 10)
        dst = [1]

        flash_binary(self.fd, data, 0x1000, '', dst)

        expected_config = {'application_size': 10, 'application_crc': crc32(data)}
        conf.assert_any_call(self.fd, expected_config, dst)

    @patch('logging.critical')
    def test_bad_board_page_erase(self, c, write):
        """
        Checks that a board who replies with an error flag during page erase
        leads to firmware upgrade halt.
        """
        ok, nok = msgpack.packb(True), msgpack.packb(False)
        write.return_value = {1: nok, 2: nok, 3: ok}  # Board 1 fails

        data = bytes([0] * 10)

        with self.assertRaises(SystemExit):
            flash_binary(None, data, 0x1000, '', [1, 2, 3])

        c.assert_any_call("Boards 1, 2 failed during page erase, aborting...")

    @patch('logging.critical')
    def test_bad_board_page_write(self, c, write):
        """
        In this scenario we test what happens if the page erase is OK, but then
        the page write fails.
        """
        ok, nok = msgpack.packb(True), msgpack.packb(False)
        side_effect = [{1: ok, 2: ok, 3: ok}]
        side_effect += [{1: nok, 2: nok, 3: ok}]  # Board 1 fails
        write.side_effect = side_effect

        data = bytes([0] * 10)

        with self.assertRaises(SystemExit):
            flash_binary(None, data, 0x1000, '', [1, 2, 3])

        c.assert_any_call("Boards 1, 2 failed during page write, aborting...")


class CANDatagramReadTestCase(unittest.TestCase):
    """
    This testcase groups all tests related to reading a datagram from the bus.
    """
    def test_read_can_datagram(self):
        """
        Tests reading a complete CAN datagram from the bus.
        """
        data = 'Hello world'.encode('ascii')
        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = can.datagram_to_frames(data, source=42)

        # Serializes CAN frames for the bridge
        frames = [can_bridge.frame.encode(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = BytesIO(frames)

        reader = CANDatagramReader(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = reader.read_datagram()

        self.assertEqual(dt.decode('ascii'), 'Hello world')
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)

    def test_drop_extended_frames(self):
        """
        Checks that we drop extended frames
        """
        data = 'Hello world'.encode('ascii')
        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = list(can.datagram_to_frames(data, source=42))

        # Add an extended frame, with an annoying ID
        id = frames[0].id
        frames = [can_bridge.frame.Frame(extended=True, data=bytes([1, 2, 3]), id=id)] + frames

        # Serializes CAN frames for the bridge
        frames = [can_bridge.frame.encode(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = BytesIO(frames)

        reader = CANDatagramReader(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = reader.read_datagram()

        self.assertEqual(dt.decode('ascii'), 'Hello world')
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)



    def test_read_can_interleaved_datagrams(self):
        """
        Tests reading two interleaved CAN datagrams together.
        """

        data = 'Hello world'.encode('ascii')
        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = [can.datagram_to_frames(data, source=i) for i in range(2)]

        # Interleave frames
        frames = [x for t in zip(*frames) for x in t]

        # Serializes CAN frames for the bridge
        frames = [can_bridge.frame.encode(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = BytesIO(frames)

        decode = CANDatagramReader(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = decode.read_datagram()

    def test_read_several_datagrams_from_src(self):
        """
        Checks if we can read several datagrams from the same source.
        """
        data = bytes()

        for i in range(2):
            # Encapsulates it in a CAN datagram
            dt = can.encode_datagram(bytes(), destinations=[i])
            frames = can.datagram_to_frames(dt, source=1)
            frames = [can_bridge.frame.encode(f) for f in frames]
            frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)
            data += frames

        fdesc = BytesIO(data)
        decode = CANDatagramReader(fdesc)

        # Read a CAN datagram from that pseudofile
        _, dst, _ = decode.read_datagram()
        self.assertEqual([0], dst)

        _, dst, _ = decode.read_datagram()
        self.assertEqual([1], dst)



    def test_read_can_datagram_timeout(self):
        """
        Tests reading a datagram with a timeout (read_datagram returns None).
        """
        data = 'Hello world'.encode('ascii')

        reader = CANDatagramReader(None)

        with patch('serial_datagrams.read_datagram') as read:
            read.return_value = None
            a = reader.read_datagram()

        self.assertIsNone(a)

class ConfigTestCase(unittest.TestCase):
    fd = "port"

    @patch('utils.write_command_retry')
    def test_config_is_updated_and_saved(self, write):
        """
        Checks that the config is correctly sent encoded to the board.
        We then check if the config is saved to flash.
        """
        config = {'id':14}
        dst = [1]
        update_call = call(self.fd, encode_update_config(config), dst)
        save_command = call(self.fd, encode_save_config(), dst)

        config_update_and_save(self.fd, config, [1])

        # Checks that the calls were made, and in the correct order
        write.assert_has_calls([update_call, save_command])

    @patch('utils.CANDatagramReader.read_datagram')
    @patch('utils.write_command')
    def test_check_single_valid_checksum(self, write, read_datagram):
        """
        Checks what happens if there are invalid checksums.
        """
        binary = bytes([0] * 10)
        crc = crc32(binary)

        side_effect  = [(msgpack.packb(crc), [0], 1)]
        side_effect += [(msgpack.packb(0xdead), [0], 2)]
        side_effect += [None] # timeout

        read_datagram.side_effect = side_effect


        valid_nodes = check_binary(self.fd, binary, 0x1000, [1, 2])

        self.assertEqual([1], valid_nodes)

    @patch('utils.CANDatagramReader.read_datagram')
    @patch('utils.write_command')
    def test_verify_handles_timeout(self, write, read_datagram):
        """
        When working with large firmwares, the connection may timeout before
        answering (issue #53).
        """
        binary = bytes([0] * 10)
        crc = crc32(binary)

        side_effect  = [None] # timeout
        side_effect += [(msgpack.packb(0xdead), [0], 2)]
        side_effect += [(msgpack.packb(crc), [0], 1)]

        read_datagram.side_effect = side_effect

        valid_nodes = check_binary(self.fd, binary, 0x1000, [1, 2])

        self.assertEqual([1], valid_nodes)

class RunApplicationTestCase(unittest.TestCase):
    fd = 'port'

    @patch('utils.write_command')
    def test_run_application(self, write):
        run_application(self.fd, [1])

        command = commands.encode_jump_to_main()
        write.assert_any_call(self.fd, command, [1])

class MainTestCase(unittest.TestCase):
    """
    Tests for the main function of the program.

    Since the code has a good coverage and is quite complex, there is an
    extensive use of mocking in those tests to replace all collaborators.
    """
    def setUp(self):
        """
        Function that runs before each test.

        The main role of this function is to prepare all mocks that are used in
        main, setup fake file and devices etc.
        """
        mock = lambda m: patch(m).start()
        self.open = mock('builtins.open')
        self.print = mock('builtins.print')

        self.serial = mock('serial.Serial')
        self.serial_device = Mock()
        self.serial.return_value = self.serial_device

        self.flash = mock('bootloader_flash.flash_binary')
        self.check = mock('bootloader_flash.check_binary')
        self.run = mock('bootloader_flash.run_application')

        self.check_online_boards = mock('bootloader_flash.check_online_boards')
        self.check_online_boards.side_effect = lambda f, b: set([1,2,3])

        # Prepare binary file argument
        self.binary_data = bytes([0] * 10)
        self.open.return_value = BytesIO(self.binary_data)

        # Flash checking results
        self.check.return_value = [1,2,3] # all boards are ok

        # Populate command line arguments
        sys.argv = "test.py -b test.bin -a 0x1000 -p /dev/ttyUSB0 -c dummy 1 2 3".split()

    def tearDown(self):
        """
        function run after each test.
        """
        # Deactivate all mocks
        patch.stopall()

    def test_open_file(self):
        """
        Checks that the correct file is opened.
        """
        main()
        self.open.assert_any_call('test.bin', 'rb')

    def test_open_bridge_port(self):
        """
        Checks that we open the correct serial port to the bridge.
        """
        main()
        self.serial.assert_any_call(port='/dev/ttyUSB0', baudrate=115200, timeout=0.2)

    def test_failing_ping(self):
        """
        Checks what happens if a board doesn't pingback.
        """
        # No board answers
        self.check_online_boards.side_effect = lambda f, b: set()

        with self.assertRaises(SystemExit):
            main()


    def test_flash_binary(self):
        """
        Checks that the binary file is flashed correctly.
        """
        main()
        self.flash.assert_any_call(self.serial_device, self.binary_data, 0x1000, 'dummy', [1,2,3])

    def test_check(self):
        """
        Checks that the flash is verified.
        """
        main()
        self.check.assert_any_call(self.serial_device, self.binary_data, 0x1000, [1,2,3])


    def test_check_failed(self):
        """
        Checks that the program behaves correctly when verification fails.
        """
        self.check.return_value = [1]
        with patch('bootloader_flash.verification_failed') as failed:
            main()
            failed.assert_any_call(set((2,3)))

    def test_do_not_run_by_default(self):
        """
        Checks that by default no run command are ran.
        """
        main()
        self.assertFalse(self.run.called)

    def test_run_if_asked(self):
        """
        Checks if we can can ask the board to run.
        """
        sys.argv += ["--run"]
        main()
        self.run.assert_any_call(self.serial_device, [1,2,3])




    def test_verification_failed(self):
        """
        Checks that the verification failed method works as expected.
        """
        with self.assertRaises(SystemExit):
            verification_failed([1,2])

        self.print.assert_any_call('Verification failed for nodes 1, 2')

class ArgumentParsingTestCase(unittest.TestCase):
    """
    All tests related to argument parsing.
    """

    def test_simple_case(self):
        """
        Tests the most simple case.
        """
        commandline = "-b test.bin -a 0x1000 -p /dev/ttyUSB0 --run -c dummy 1 2 3"
        args = parse_commandline_args(commandline.split())
        self.assertEqual('test.bin', args.binary_file)
        self.assertEqual(0x1000, args.base_address)
        self.assertEqual('/dev/ttyUSB0', args.serial_device)
        self.assertEqual('dummy', args.device_class)
        self.assertEqual([1,2,3], args.ids)
        self.assertTrue(args.run)

    def test_network_hostname(self):
        """
        Checks that we can pass a hostname
        """
        commandline = "-b test.bin -a 0x1000 --tcp 10.0.0.10 --run -c dummy 1 2 3"
        args = parse_commandline_args(commandline.split())
        self.assertEqual(None, args.serial_device)
        self.assertEqual("10.0.0.10", args.hostname)

    def test_network_hostname_or_serial_is_required(self):
        """
        Checks that we have either a serial device or a TCP/IP host to use.
        """
        commandline = "-b test.bin -a 0x1000 --run -c dummy 1 2 3"

        with patch('argparse.ArgumentParser.error') as error:
            parse_commandline_args(commandline.split())

            # Checked that we printed some kind of error
            error.assert_any_call(ANY)

    def test_network_hostname_or_serial_are_exclusive(self):
        """
        Checks that the serial device and the TCP/IP host are mutually exclusive.
        """
        commandline = "-b test.bin -a 0x1000 -p /dev/ttyUSB0 --tcp 10.0.0.10 --run -c dummy 1 2 3"

        with patch('argparse.ArgumentParser.error') as error:
            parse_commandline_args(commandline.split())

            # Checked that we printed some kind of error
            error.assert_any_call(ANY)

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

            self.assertEqual(port, serial.return_value)
            serial.assert_any_call(port="/dev/ttyUSB0", baudrate=ANY, timeout=ANY)

    def test_open_hostname_default_port(self):
        """
        Checks that we can open a connection to a hostname with the default port.
        """
        args = self.make_args(hostname="10.0.0.10")

        with patch('socket.create_connection') as create_connection:
            socket = Mock(return_value=object())

            create_connection.return_value = Mock()
            port = open_connection(args)

            create_connection.assert_any_call(('10.0.0.10', 1337))

            self.assertEqual(port.socket, create_connection.return_value)

    def test_open_hostname_custom_port(self):
        """
        Checks if we can open a connection to a hostname on a different port.
        """
        args = self.make_args(hostname="10.0.0.10:42")
        with patch('socket.create_connection') as create_connection:
            port = open_connection(args)
            create_connection.assert_any_call(('10.0.0.10', 42))
