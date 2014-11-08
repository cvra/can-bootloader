import unittest
import struct
from uart_datagrams import *

class UARTDatagramEncodeTestCase(unittest.TestCase):
    def test_crc_encapsulation(self):
        """
        Checks that the CRC is correctly encapsulated at the end of the datagram.
        """
        data = bytes([0] * 3)
        expected_crc = struct.pack('>I', 4282505490)

        datagram = datagram_encode(data)
        self.assertEqual(expected_crc, datagram[-5:-1], "CRC mismatch")

    def test_end_marker(self):
        """
        Checks that the end marker is added.
        """
        data = bytes([0] * 3)
        datagram = datagram_encode(data)
        self.assertEqual(0xc0, datagram[-1], "No end marker")

    def test_end_is_replaced(self):
        """
        Checks that the end byte is escaped.
        """
        data = bytes([0xc0]) # end marker is 0xDB
        datagram = datagram_encode(data)
        expected = bytes([0xdb, 0xdc]) # transposed end

        self.assertEqual(expected, datagram[0:2], "END was not correctly escaped")

    def test_esc_is_escaped(self):
        """
        Checks that the ESC byte is escaped.
        """

        data = bytes([0xdb]) # esc marker
        datagram = datagram_encode(data)
        expected = bytes([0xdb, 0xdd]) # transposed esc
        self.assertEqual(expected, datagram[0:2], "ESC was not correctly escaped")


