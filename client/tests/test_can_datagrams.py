import unittest
from struct import unpack_from, pack
from zlib import crc32
from can import *

try:
    import unittest.mock as mock
except ImportError:
    import mock




class CanDatagramTestCase(unittest.TestCase):
    data = 'hello, world'.encode('ascii')

    def test_can_encode_single_destination(self):
        """
        This test checks if we can encode a single destination in the datagram.
        """
        destinations = [10]
        dt = encode_datagram(destinations, self.data)

        # Destination nodes length
        self.assertEqual(dt[4], 1)

        # Destination nodes list
        self.assertEqual(dt[5], 10)

    def test_can_encode_multiple_destinations(self):
        """
        This test checks if we can encode several destinations.
        """
        dt = encode_datagram([1,2,3], self.data)

        # Length
        self.assertEqual(dt[4], 3)

        # Nodes
        self.assertEqual(dt[5:8], bytes([1,2,3]))

    def test_can_encode_data_length(self):
        """
        Checks if we can read data length.
        """
        dt = encode_datagram([1], self.data)
        data_length = unpack_from('>I', dt, 4 + 2)[0]
        self.assertEqual(len(self.data), data_length)

    def test_can_add_data(self):
        """
        Checks if we can add data.
        """
        dt = encode_datagram([1], self.data)
        data = dt[4 + 1 + 1 + 4:]
        self.assertEqual(data, self.data)

    def test_crc_is_at_the_correct_place(self):
        """
        Checks that the first 4 bytes are made of the crc.
        """
        data = 'hello'.encode('ascii')
        expected = pack('>I', crc32(bytes([1,1,0,0,0,5]) + data))
        crc = encode_datagram([1], data)[:4]
        self.assertEqual(crc, expected)




