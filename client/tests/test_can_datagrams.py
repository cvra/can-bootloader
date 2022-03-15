import unittest
from struct import unpack_from, pack
from zlib import crc32
from cvra_bootloader.can import *

try:
    import unittest.mock as mock
except ImportError:
    import mock


class CanDatagramTestCase(unittest.TestCase):
    data = "hello, world".encode("ascii")

    def test_encode_datagram_version(self):
        """
        This test checks if we can properly encode the datagram version.
        """
        dt = encode_datagram(self.data, [1])
        self.assertEqual(DATAGRAM_VERSION, dt[0])
        pass

    def test_can_encode_single_destination(self):
        """
        This test checks if we can encode a single destination in the datagram.
        """
        dt = encode_datagram(self.data, [10])

        # Destination nodes length
        self.assertEqual(dt[5], 1)

        # Destination nodes list
        self.assertEqual(dt[6], 10)

    def test_can_encode_multiple_destinations(self):
        """
        This test checks if we can encode several destinations.
        """
        dt = encode_datagram(self.data, [1, 2, 3])

        # Length
        self.assertEqual(dt[5], 3)

        # Nodes
        self.assertEqual(dt[6:9], bytes([1, 2, 3]))

    def test_can_encode_data_length(self):
        """
        Checks if we can read data length.
        """
        dt = encode_datagram(self.data, [1])
        data_length = unpack_from(">I", dt, 1 + 4 + 2)[0]
        self.assertEqual(len(self.data), data_length)

    def test_can_add_data(self):
        """
        Checks if we can add data.
        """
        dt = encode_datagram(self.data, [1])
        data = dt[1 + 4 + 1 + 1 + 4 :]
        self.assertEqual(data, self.data)

    def test_crc_is_at_the_correct_place(self):
        """
        Checks that the 4 bytes after the version are made of the crc.
        """
        data = "hello".encode("ascii")
        expected = pack(">I", crc32(bytes([1, 1, 0, 0, 0, 5]) + data))
        crc = encode_datagram(data, [1])[1:5]
        self.assertEqual(crc, expected)

    def test_frame_too_long_raises_valueerror(self):
        """
        This test checks that building a Frame longer than 8 bytes raises a
        ValueError.
        """
        with self.assertRaises(ValueError):
            Frame(data=bytes(range(10)))

    def assertBitSet(self, value, bit):
        value = value & (1 << bit)
        self.assertTrue(value, "Bit {} not set".format(bit))

    def assertBitClear(self, value, bit):
        value = value & (1 << bit)
        self.assertFalse(value, "Bit {} not set".format(bit))

    def test_assertbit(self):
        self.assertBitSet(3, 1)
        self.assertBitClear(2, 0)

        with self.assertRaises(AssertionError):
            self.assertBitSet(3, 5)

        with self.assertRaises(AssertionError):
            self.assertBitClear(2, 1)

    def test_datagram_start_bit(self):
        """
        Checks if the start bit is encoded correctly.
        """
        dt = encode_datagram(bytes(), [1])
        msgs = datagram_to_frames(dt, source=0)

        # Bit 7 is start bit.
        self.assertBitSet(next(msgs).id, 7)
        self.assertBitClear(next(msgs).id, 7)

    def test_datagram_source_id(self):
        """
        Checks that the source indication is encoded correctly.
        """
        dt = encode_datagram(bytes(), [1])
        msgs = datagram_to_frames(dt, source=42)

        # 7 first bits are source ID
        mask = 0x7F

        # Checks that the id is correct for all frams
        self.assertEqual(next(msgs).id & mask, 42)
        self.assertEqual(next(msgs).id & mask, 42)

    def test_datagram_has_all_data(self):
        """
        Checks that grouping all frames makes the whole datagram.
        """
        dt = encode_datagram(bytes(range(10)), [1])
        msgs = datagram_to_frames(dt, source=42)

        # Concatenate all data in datagrams
        recomposed_data = [b for m in msgs for b in m.data]

        self.assertEqual(recomposed_data, list(dt))

    def test_receive_datagram(self):
        """
        Checks that we can correctly decode data of a received datagram.
        """
        dt = encode_datagram(bytes([1, 2, 3]), [1])
        data, dst = decode_datagram(dt)
        self.assertEqual(dst, [1])
        self.assertEqual(data, bytes([1, 2, 3]))

    def test_receive_incomplete_datagram(self):
        """
        Checks that we get None if the datagram is incomplete.
        """
        dt = encode_datagram(bytes([1, 2, 3]), [1])
        dt = dt[:4]  # remove end of datagram
        self.assertIsNone(decode_datagram(dt))

    def test_receive_incomplete_datagram_data(self):
        """
        Checks that we return None if the datagram data are incomplete
        """
        dt = encode_datagram(bytes([1, 2, 3]), [1])
        dt = dt[:-1]  # remove end of datagram
        self.assertIsNone(decode_datagram(dt))

    def test_wrong_version_raise_exception(self):
        """
        Checks that receiving a datagram with wrong version raises an exception.
        """
        dt = encode_datagram(bytes([1, 2, 3]), [1])
        dt = bytes([0]) + dt[1:]  # set version field to zero

        with self.assertRaises(VersionMismatchError):
            decode_datagram(dt)

    def test_wrong_crc_raise_exception(self):
        """
        Checks that decoding a datagram with the wrong CRC raises an exception.
        """
        dt = encode_datagram(bytes([1, 2, 3]), [1])

        # Change last byte, invalidating CRC
        dt = dt[:-1] + bytes([42])

        with self.assertRaises(CRCMismatchError):
            decode_datagram(dt)

    def test_that_datagram_start_is_detected_correctly(self):
        """
        This test checks that the start of datagram marker on a frame is
        detected correctly.
        """
        self.assertFalse(is_start_of_datagram(Frame(id=2)))
        self.assertTrue(is_start_of_datagram(Frame(id=2 + (1 << 7))))
