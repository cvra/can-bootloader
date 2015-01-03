import unittest
from unittest.mock import Mock, patch, ANY, call
from serial import Serial
from zlib import crc32

from bootloader_flash import *
from commands import *

class FlashBinaryTestCase(unittest.TestCase):
    fd = "port"

    @patch('bootloader_flash.write_command')
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


    @patch('bootloader_flash.write_command')
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

    @patch('bootloader_flash.write_command')
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

    @patch('bootloader_flash.write_command')
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

    @patch('bootloader_flash.write_command')
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

