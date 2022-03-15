import unittest
from cvra_bootloader.commands import *
from msgpack import Unpacker


class ProtocolVersionTestCase(unittest.TestCase):
    """
    This testcase checks that the command set version is correctly handled.
    """

    def test_has_correct_protocol_version(self):
        """
        Checks that the command encoding function works corectly.
        """
        raw_packet = encode_command(command_code=10)

        unpacker = Unpacker()
        unpacker.feed(raw_packet)

        version, *_ = list(unpacker)
        self.assertEqual(2, version)


class WriteCommandTestCase(unittest.TestCase):
    """
    This testcase checks if the command used to write to a page functions correctly.

    See README.markdown for more information on the command format.
    """

    def setUp(self):
        address = 0xDEADBEEF
        data = bytes(range(4))
        device = "dummy"

        raw_packet = encode_write_flash(data, address, device)

        unpacker = Unpacker()
        unpacker.feed(raw_packet)
        # Discards command set version
        self.command = list(unpacker)[1:]

    def test_command_has_correct_index(self):
        """
        Checks that the command index is correct. It should be 0x3.
        """
        index = self.command[0]
        self.assertEqual(CommandType.Write, index)

    def test_command_has_correct_address(self):
        """
        Checks that the address is put at the correct place in the command.
        """
        address = self.command[1][0]
        self.assertEqual(0xDEADBEEF, address)

    def test_device_class(self):
        """
        Checks that the third element of the command is the device class.
        """
        device = self.command[1][1].decode("ascii")
        self.assertEqual("dummy", device)

    def test_device_data(self):
        """
        Checks that the last item is the data.
        """
        data = self.command[1][2]
        self.assertEqual(bytes([0, 1, 2, 3]), data)

    def test_write_command_use_binary_type(self):
        """
        Checks that the write command uses bin type.
        """
        raw_packet = encode_write_flash(bytes([12]), address=1, device_class="dummy")

        # 0xc4 is binary type marker
        self.assertEqual(raw_packet[-3], 0xC4)

        # 1 is length
        self.assertEqual(raw_packet[-2], 1)

        # Finally data
        self.assertEqual(raw_packet[-1], 12)


class EraseCommandTestCase(unittest.TestCase):
    """
    Tests for the erase flash page command.
    """

    def setUp(self):
        address = 0xFA1AFE1
        device = "LivewareProblem"

        raw_packet = encode_erase_flash_page(address, device)

        unpacker = Unpacker()
        unpacker.feed(raw_packet)
        self.command = list(unpacker)[1:]

    def test_erase_command_index(self):
        """
        Checks that the index for the command is correct.
        """
        self.assertEqual(self.command[0], CommandType.Erase)

    def test_erase_command_address(self):
        """
        Checks that the page addres is correct.
        """
        self.assertEqual(self.command[1][0], 0xFA1AFE1)

    def test_erase_command_device(self):
        """
        Checks that the device name is correct.
        """
        self.assertEqual(self.command[1][1].decode("ascii"), "LivewareProblem")


class JumpToApplicationMainTestCase(unittest.TestCase):
    """
    Tests for the jump to application main command.
    """

    def setUp(self):
        raw_packet = encode_jump_to_main()
        unpacker = Unpacker()
        unpacker.feed(raw_packet)
        self.command = list(unpacker)[1:]

    def test_jump_cmd_index(self):
        """
        Checks that the index for the command is correct.
        """
        self.assertEqual(self.command[0], CommandType.JumpToMain)


class PingTestCase(unittest.TestCase):
    """
    Checks that the ping command is properly encoded.
    """

    def setUp(self):
        raw_packet = encode_ping()
        unpacker = Unpacker()
        unpacker.feed(raw_packet)
        self.command = list(unpacker)[1:]

    def test_ping(self):
        self.assertEqual(self.command[0], 5)
