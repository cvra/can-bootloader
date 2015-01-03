import unittest

try:
    from unittest.mock import *
except ImportError:
    from mock import *

from serial import Serial
from zlib import crc32

from bootloader_flash import *
from commands import *
import msgpack

from io import BytesIO

import can, serial_datagrams, can_bridge

@patch('bootloader_flash.write_command')
class FlashBinaryTestCase(unittest.TestCase):
    fd = "port"

    def test_single_page_erase(self, write):
        """
        Checks that a single page is erased before writing.
        """
        data = bytes(range(20))
        adress = 0x1000
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, data, adress, "dummy", destinations)

        erase_command = encode_erase_flash_page(adress, device_class)
        write.assert_any_call(self.fd, erase_command, destinations)

    def test_write_single_chunk(self, write):
        """
        Tests that a single chunk can be written.
        """
        data = bytes(range(20))
        adress = 0x1000
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, data, adress, "dummy", [1])

        write_command = encode_write_flash(data, adress, device_class)

        write.assert_any_call(self.fd, write_command, destinations)

    def test_write_many_chunks(self, write):
        """
        Checks that we can write many chunks, but still in one page
        """
        data = bytes([0] * 4096)
        adress = 0x1000
        device_class = 'dummy'
        destinations = [1]

        flash_binary(self.fd, data, adress, "dummy", [1])

        write_command = encode_write_flash(bytes([0] * 2048), adress, device_class)
        write.assert_any_call(self.fd, write_command, destinations)

        write_command = encode_write_flash(bytes([0] * 2048), adress + 2048, device_class)
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

    @patch('bootloader_flash.config_update_and_save')
    def test_crc_is_updated(self, conf, write):
        """
        Tests that the CRC is updated after flashing a binary.
        """
        data = bytes([0] * 10)
        dst = [1]

        flash_binary(self.fd, data, 0x1000, '', dst)

        expected_config = {'application_size': 10, 'application_crc': crc32(data)}
        conf.assert_any_call(self.fd, expected_config, dst)

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
        frames = can.datagram_to_frames(data, source=0)

        # Serializes CAN frames for the bridge
        frames = [can_bridge.encode_frame(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = BytesIO(frames)

        # Read a CAN datagram from that pseudofile
        dt, dst = read_can_datagram(fdesc)

        self.assertEqual(dt.decode('ascii'), 'Hello world')
        self.assertEqual(dst, [1])




class ConfigTestCase(unittest.TestCase):
    fd = "port"

    @patch('bootloader_flash.write_command')
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

class CrcRegionTestCase(unittest.TestCase):
    fd = 'port'

    @patch('bootloader_flash.write_command')
    @patch('bootloader_flash.read_can_datagram')
    def test_read_crc_sends_command(self, read, write):
        """
        Checks that a CRC read sends the correct command.
        """
        read.return_value = msgpack.packb(0xdeadbeef)

        crc_region(fdesc=self.fd, base_address=0x1000, length=100, destination=42)
        command = commands.encode_crc_region(0x1000, 100)
        write.assert_any_call(self.fd, command, [42])

    @patch('bootloader_flash.write_command')
    @patch('bootloader_flash.read_can_datagram')
    def test_read_crc_answer(self, read, write):
        """
        Checks that we can read back the CRC answer.
        """
        read.return_value = msgpack.packb(0xdeadbeef)
        crc = crc_region(fdesc=self.fd, base_address=0x1000, length=100, destination=42)

        # Checks that the port was given correctly
        read.assert_any_call(self.fd)

        # Checks that the CRC value matches the expected one
        self.assertEqual(0xdeadbeef, crc)

    @patch('bootloader_flash.crc_region')
    def test_single_crc(self, crc_region):
        """
        Tries to check the crc of a single node and it is valid.
        """
        binary = bytes([0] * 10)
        crc_region.return_value = crc32(binary)

        valid_nodes = check_binary(self.fd, binary, 0x1000, [1])
        self.assertEqual([1], valid_nodes)

        crc_region.assert_any_call(self.fd, 0x1000, 10, 1)

    @patch('bootloader_flash.crc_region')
    def test_check_single_valid_checksum(self, crc_region):
        """
        Checks what happens if there are invalid checksums.
        """
        binary = bytes([0] * 10)
        crc_region.side_effect = [0xbad, crc32(binary)]

        valid_nodes = check_binary(self.fd, binary, 0x1000, [1, 2])

        crc_region.assert_any_call(self.fd, 0x1000, 10, 1)
        crc_region.assert_any_call(self.fd, 0x1000, 10, 2)

        self.assertEqual([2], valid_nodes)

from unittest import skip
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

        self.parse_cli = mock('bootloader_flash.parse_commandline_args')
        self.parse_cli.return_value = Mock()

        self.serial = mock('serial.Serial')
        self.serial_device = Mock()
        self.serial.return_value = self.serial_device

        self.flash = mock('bootloader_flash.flash_binary')
        self.check = mock('bootloader_flash.check_binary')

        # Populate command line arguments
        self.parse_cli.return_value.binary_file = 'test.bin'
        self.parse_cli.return_value.serial_device = '/dev/ttyUSB0'
        self.parse_cli.return_value.device_class = 'dummy'
        self.parse_cli.return_value.base_address = 0x1000
        self.parse_cli.return_value.ids = [1,2,3]

        # Prepare binary file argument
        self.binary_data = bytes([0] * 10)
        self.open.return_value = BytesIO(self.binary_data)

        # Flash checking results
        self.check.return_value = [1,2,3] # all boards are ok

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
        self.serial.assert_any_call('/dev/ttyUSB0', baudrate=115200, timeout=0.2)

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

    def test_verification_failed(self):
        """
        Checks that the verification failed method works as expected.
        """
        with self.assertRaises(SystemExit):
            verification_failed([1,2])

        self.print.assert_any_call('Verification failed for nodes 1, 2')
