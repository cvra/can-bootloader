import unittest
import struct
from serial_datagrams import *
from io import BytesIO

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

class UARTDatagramDecodeTestCase(unittest.TestCase):
    def test_can_decode_simple_datagram(self):
        """
        Simply tries to decode a complete datagram.
        """
        datagram = [0,0,0,0xff,0x41,0xd9, 0x12, 0xC0]
        datagram = bytes(datagram)
        datagram = datagram_decode(datagram)
        self.assertEqual(bytes([0,0,0]), datagram)

    def test_invalid_crc_raises_exception(self):
        """
        Checks that having a wrong crc raises an exception.
        """
        datagram = [0,0,0,0xde, 0xad, 0xde, 0xad, 0xC0]
        datagram = bytes(datagram)
        with self.assertRaises(CRCMismatchError):
            datagram_decode(datagram)

    def test_escape_is_unescaped(self):
        """
        Checks that ESC + ESC_ESC is transformed to ESC.
        """
        datagram = b'\xdb\xdd\xc3\x03\xe4\xd1\xc0'
        datagram = datagram_decode(datagram)
        self.assertEqual(bytes([0xdb]), datagram)

    def test_end_is_unsescaped(self):
        """
        Checks that ESC + ESC_END is transformed to END.
        """
        datagram = datagram_decode(b'\xdb\xdcIf-=\xc0')
        self.assertEqual(bytes([0xc0]), datagram)

    def test_that_weird_sequences_work(self):
        """
        Decode order matters. This can be revealed by making a packet
        containing ESC + ESC_END, which would cause a problem if the replace
        happens in the wrong order.
        """
        data = ESC + ESC_END
        datagram = datagram_encode(data)
        self.assertEqual(data, datagram_decode(datagram))

    def test_that_too_short_sequence_raises_exception(self):
        """
        Checks that decoding a datagram smaller than 5 bytes (CRC + END) raises
        an exception.
        """

        with self.assertRaises(FrameError):
            datagram_decode(bytes([1,2,3,3]))


class ReadDatagramTestCase(unittest.TestCase):
    def test_can_read_datagram(self):
        """
        Checks if we can read a whole datagram.
        """
        fd = BytesIO(datagram_encode(bytes([1,2,3])))
        dt = read_datagram(fd)
        self.assertEqual(dt, bytes([1,2,3]))

    def test_what_happens_if_timeout(self):
        """
        Checks that we return None if there was a timeout.
        """
        data = datagram_encode(bytes([1,2,3]))

        # Introduce a timeout before receiving the last byte
        fd = BytesIO(data[:-1])
        self.assertIsNone(read_datagram(fd))
