import unittest

from msgpack import *

class MessagePackTestCase(unittest.TestCase):
    """
    This is not really a comprehensive test suite for messagepack but instead a
    way to learn how to use the api.
    """
    def test_can_pack_fixarray(self):
        """
        Checks that we can pack a fix array (len(array) < 16).
        """
        data = [1,2,3]
        expected = bytes([0x93, 1, 2, 3])
        self.assertEqual(expected, packb(data))

    def test_can_pack_bytes(self):
        """
        Checks that we can use binary types. By default msgpack uses str types
        for bytes() so we need to use a Packer object correctly configured.
        """
        packer = Packer(use_bin_type=True)
        data = bytes([0, 1, 2, 3])

        # Format is 0xc4, lenght, data
        expected = bytes([0xc4, 4, 0, 1, 2, 3])
        self.assertEqual(expected, packer.pack(data))
