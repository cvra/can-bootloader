import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

from zlib import crc32

from cvra_bootloader.bootloader_flash import *
from cvra_bootloader.commands import *
from cvra_bootloader.utils import *
import msgpack

from io import BytesIO

import sys


@patch("cvra_bootloader.utils.write_command_retry")
class FlashBinaryTestCase(unittest.TestCase):
    fd = "port"

    def setUp(self):
        mock = lambda m: patch(m).start()
        self.progressbar = mock("progressbar.ProgressBar")
        self.print = mock("builtins.print")

    def tearDown(self):
        patch.stopall()

    def test_single_page_erase(self, write):
        """
        Checks that a single page is erased before writing.
        """
        data = bytes(range(20))
        address = 0x1000
        device_class = "dummy"
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
        device_class = "dummy"
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
        device_class = "dummy"
        destinations = [1]

        flash_binary(self.fd, data, address, "dummy", [1])

        write_command = encode_write_flash(bytes([0] * 2048), address, device_class)
        write.assert_any_call(self.fd, write_command, destinations)

        write_command = encode_write_flash(
            bytes([0] * 2048), address + 2048, device_class
        )
        write.assert_any_call(self.fd, write_command, destinations)

    def test_erase_multiple_pages(self, write):
        """
        Checks that all pages are erased before writing data to them.
        """
        data = bytes([0] * 4096)
        device_class = "dummy"
        destinations = [1]

        flash_binary(
            self.fd,
            bytes([0] * 4096),
            0x1000,
            device_class,
            destinations,
            page_size=2048,
        )

        # Check that all pages were erased correctly
        for addr in [0x1000, 0x1800]:
            erase_command = encode_erase_flash_page(addr, device_class)
            write.assert_any_call(self.fd, erase_command, destinations)

    def test_smaller_pages(self, write):
        """
        Checks that smaller page sizes work as well.
        """
        data = bytes([0] * 4096)
        address = 0x1000
        device_class = "dummy"
        destinations = [1]

        flash_binary(
            self.fd,
            binary=bytes(4096),
            base_address=0x1000,
            device_class="dummy",
            destinations=[1],
            page_size=16,
        )

        # Check that we werased everything
        for addr in range(0x1000, 0x1000 + 4096, 16):
            erase_cmd = encode_erase_flash_page(addr, device_class)
            write.assert_any_call(self.fd, erase_cmd, destinations)

            write_cmd = encode_write_flash(bytes(16), addr, device_class)
            write.assert_any_call(self.fd, write_cmd, destinations)

    @patch("cvra_bootloader.utils.config_update_and_save")
    def test_crc_is_updated(self, conf, write):
        """
        Tests that the CRC is updated after flashing a binary.
        """
        data = bytes([0] * 10)
        dst = [1]

        flash_binary(self.fd, data, 0x1000, "", dst)

        expected_config = {"application_size": 10, "application_crc": crc32(data)}
        conf.assert_any_call(self.fd, expected_config, dst)

    @patch("logging.critical")
    def test_bad_board_page_erase(self, c, write):
        """
        Checks that a board who replies with an error flag during page erase
        leads to firmware upgrade halt.
        """
        ok, nok = msgpack.packb(True), msgpack.packb(False)
        write.return_value = {1: nok, 2: nok, 3: ok}  # Board 1 fails

        data = bytes([0] * 10)

        with self.assertRaises(SystemExit):
            flash_binary(None, data, 0x1000, "", [1, 2, 3])

        c.assert_any_call("Boards 1, 2 failed during page erase, aborting...")

    @patch("logging.critical")
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
            flash_binary(None, data, 0x1000, "", [1, 2, 3])

        c.assert_any_call("Boards 1, 2 failed during page write, aborting...")


class ConfigTestCase(unittest.TestCase):
    fd = "port"

    @patch("cvra_bootloader.utils.write_command_retry")
    def test_config_is_updated_and_saved(self, write):
        """
        Checks that the config is correctly sent encoded to the board.
        We then check if the config is saved to flash.
        """
        config = {"id": 14}
        dst = [1]
        update_call = call(self.fd, encode_update_config(config), dst)
        save_command = call(self.fd, encode_save_config(), dst)

        config_update_and_save(self.fd, config, [1])

        # Checks that the calls were made, and in the correct order
        write.assert_has_calls([update_call, save_command])

    @patch("cvra_bootloader.utils.read_can_datagrams")
    @patch("cvra_bootloader.utils.write_command")
    def test_check_single_valid_checksum(self, write, read_datagram):
        """
        Checks what happens if there are invalid checksums.
        """
        binary = bytes([0] * 10)
        crc = crc32(binary)

        side_effect = [(msgpack.packb(crc), [0], 1)]
        side_effect += [(msgpack.packb(0xDEAD), [0], 2)]
        side_effect += [None]  # timeout

        read_datagram.return_value = iter(side_effect)

        valid_nodes = check_binary(self.fd, binary, 0x1000, [1, 2])

        self.assertEqual([1], valid_nodes)

    @patch("cvra_bootloader.utils.read_can_datagrams")
    @patch("cvra_bootloader.utils.write_command")
    def test_verify_handles_timeout(self, write, read_datagram):
        """
        When working with large firmwares, the connection may timeout before
        answering (issue #53).
        """
        binary = bytes([0] * 10)
        crc = crc32(binary)

        side_effect = [None]  # timeout
        side_effect += [(msgpack.packb(0xDEAD), [0], 2)]
        side_effect += [(msgpack.packb(crc), [0], 1)]

        read_datagram.return_value = iter(side_effect)

        valid_nodes = check_binary(self.fd, binary, 0x1000, [1, 2])

        self.assertEqual([1], valid_nodes)


class RunApplicationTestCase(unittest.TestCase):
    fd = "port"

    @patch("cvra_bootloader.utils.write_command")
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
        self.open = mock("builtins.open")
        self.print = mock("builtins.print")

        self.open_conn = mock("cvra_bootloader.utils.open_connection")
        self.conn = Mock()
        self.open_conn.return_value = self.conn

        self.flash = mock("cvra_bootloader.bootloader_flash.flash_binary")
        self.check = mock("cvra_bootloader.bootloader_flash.check_binary")
        self.run = mock("cvra_bootloader.bootloader_flash.run_application")

        self.check_online_boards = mock(
            "cvra_bootloader.bootloader_flash.check_online_boards"
        )
        self.check_online_boards.side_effect = lambda f, b: set([1, 2, 3])

        # Prepare binary file argument
        self.binary_data = bytes([0] * 10)
        self.open.return_value = BytesIO(self.binary_data)

        # Flash checking results
        self.check.return_value = [1, 2, 3]  # all boards are ok

        # Populate command line arguments
        sys.argv = (
            "test.py -b test.bin -a 0x1000 -p /dev/ttyUSB0 -c dummy 1 2 3".split()
        )

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
        self.open.assert_any_call("test.bin", "rb")

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
        self.flash.assert_any_call(
            self.conn, self.binary_data, 0x1000, "dummy", [1, 2, 3], page_size=ANY
        )

    def test_check(self):
        """
        Checks that the flash is verified.
        """
        main()
        self.check.assert_any_call(self.conn, self.binary_data, 0x1000, [1, 2, 3])

    def test_check_failed(self):
        """
        Checks that the program behaves correctly when verification fails.
        """
        self.check.return_value = [1]
        with patch("cvra_bootloader.bootloader_flash.verification_failed") as failed:
            main()
            failed.assert_any_call(set((2, 3)))

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
        self.run.assert_any_call(self.conn, [1, 2, 3])

    def test_change_page_size(self):
        """
        Checks that we can change the page size.
        """
        sys.argv += ["--page-size=16"]
        main()
        self.flash.assert_any_call(ANY, ANY, ANY, ANY, ANY, page_size=16)

    def test_verification_failed(self):
        """
        Checks that the verification failed method works as expected.
        """
        with self.assertRaises(SystemExit):
            verification_failed([1, 2])

        self.print.assert_any_call("Verification failed for nodes 1, 2")


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
        self.assertEqual("test.bin", args.binary_file)
        self.assertEqual(0x1000, args.base_address)
        self.assertEqual("/dev/ttyUSB0", args.serial_device)
        self.assertEqual("dummy", args.device_class)
        self.assertEqual([1, 2, 3], args.ids)
        self.assertTrue(args.run)

    def test_can_interface_argument(self):
        """
        Checks that we can pass CAN interface
        """
        commandline = "-b test.bin -a 0x1000 --interface /dev/can0 --run -c dummy 1 2 3"
        args = parse_commandline_args(commandline.split())
        self.assertEqual(None, args.serial_device)
        self.assertEqual("/dev/can0", args.can_interface)

    def test_can_interface_or_serial_is_required(self):
        """
        Checks that we have either a serial device or a CAN interface to use.
        """
        commandline = "-b test.bin -a 0x1000 --run -c dummy 1 2 3"

        with patch("argparse.ArgumentParser.error") as error:
            parse_commandline_args(commandline.split())

            # Checked that we printed some kind of error
            error.assert_any_call(ANY)

    def test_can_interface_or_serial_are_exclusive(self):
        """
        Checks that the serial device and the CAN interface are mutually exclusive.
        """
        commandline = "-b test.bin -a 0x1000 -p /dev/ttyUSB0 --interface /dev/can0 --run -c dummy 1 2 3"

        with patch("argparse.ArgumentParser.error") as error:
            parse_commandline_args(commandline.split())

            # Checked that we printed some kind of error
            error.assert_any_call(ANY)

    def test_page_size(self):
        """
        Checks that we can change the page size.
        """
        cmd = "-b test.bin -a 0x1000 -p /dev/ttyUSB0 -c dummy 1".split()
        self.assertEqual(
            2048, parse_commandline_args(cmd).page_size, "Invalid page size"
        )
        cmd += "--page-size 10".split()
        self.assertEqual(10, parse_commandline_args(cmd).page_size, "Invalid page size")
