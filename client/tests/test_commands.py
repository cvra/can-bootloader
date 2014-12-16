import unittest
from commands import *
from msgpack import Unpacker

class WriteCommandTestCase(unittest.TestCase):
    """
    This testcase checks if the command used to write to a page functions correctly.

    See README.markdown for more information on the command format.
    """

    def setUp(self):
        adress = 0xdeadbeef
        data = bytes(range(4))
        device = "dummy"

        raw_packet = encode_write_flash(data, adress, device)

        unpacker = Unpacker()
        unpacker.feed(raw_packet)
        self.command = list(unpacker)

    def test_command_has_correct_index(self):
        """
        Checks that the command index is correct. It should be 0x3.
        """
        index = self.command[0]
        self.assertEqual(3, index)

    def test_command_has_correct_adress(self):
        """
        Checks that the adress is put at the correct place in the command.
        """
        adress = self.command[1][0]
        self.assertEqual(0xdeadbeef, adress)

    def test_device_class(self):
        """
        Checks that the third element of the command is the device class.
        """
        device = self.command[1][1].decode('ascii')
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
        raw_packet = encode_write_flash(bytes([12]), adress=1, device_class="dummy")

        # 0xc4 is binary type marker
        self.assertEqual(raw_packet[-3], 0xc4)

        # 1 is length
        self.assertEqual(raw_packet[-2], 1)

        # Finally data
        self.assertEqual(raw_packet[-1], 12)

class JumpToApplicationMainTestCase(unittest.TestCase):
    """
    Tests for the jump to application main command.
    """
    def setUp(self):
        raw_packet = encode_jump_to_main()
        unpacker = Unpacker()
        unpacker.feed(raw_packet)
        self.command = list(unpacker)

    def test_jump_cmd_index(self):
        """
        Checks that the index for the command is correct.
        """
        self.assertEqual(self.command[0], 1)

