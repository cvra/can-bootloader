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
        dt = encode_datagram(self.data, [1,2,3])

        # Length
        self.assertEqual(dt[5], 3)

        # Nodes
        self.assertEqual(dt[6:9], bytes([1,2,3]))

    def test_can_encode_data_length(self):
        """
        Checks if we can read data length.
        """
        dt = encode_datagram(self.data, [1])
        data_length = unpack_from('>I', dt, 1 + 4 + 2)[0]
        self.assertEqual(len(self.data), data_length)

    def test_can_add_data(self):
        """
        Checks if we can add data.
        """
        dt = encode_datagram(self.data, [1])
        data = dt[1 + 4 + 1 + 1 + 4:]
        self.assertEqual(data, self.data)

    def test_crc_is_at_the_correct_place(self):
        """
        Checks that the 4 bytes after the version are made of the crc.
        """
        data = 'hello'.encode('ascii')
        expected = pack('>I', crc32(bytes([1,1,0,0,0,5]) + data))
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
        mask = 0x7f

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

    def test_datagram_can_receive(self):
        """
        Checks if datagrams are received correctly
        """
        rec = ReceiveDatagram()
        data = bytes("hello world!", 'ascii')
        dest_ids = [23, 42]
        ret = rec.input_data(encode_datagram(data, dest_ids))
        self.assertEqual(ret, True)
        self.assertEqual(rec.data, data)
        self.assertEqual(rec.dest, dest_ids)
        self.assertEqual(rec.dest_len, len(dest_ids))
        self.assertEqual(rec.version, DATAGRAM_VERSION)

    def test_datagram_can_receive_from_multiple(self):
        """
        Checks if datagrams are received correctly from multiple frames
        """
        rec = ReceiveDatagram()
        data = bytes("hello world!", 'ascii')
        dest_ids = [23, 42]
        frames = datagram_to_frames(encode_datagram(data, dest_ids), 1)
        for f in frames:
            ret = rec.input_data(f.data)
        self.assertEqual(ret, True)
        self.assertEqual(rec.data, data)
        self.assertEqual(rec.dest, dest_ids)
        self.assertEqual(rec.dest_len, len(dest_ids))
        self.assertEqual(rec.version, DATAGRAM_VERSION)

    def test_datagram_can_detect_version_error(self):
        """
        Checks if a datagram version error is detected
        """
        rec = ReceiveDatagram()
        dt = encode_datagram(bytes("hello world!", 'ascii'), [23, 42])
        # alter crc
        alt_dt = struct.pack('B', DATAGRAM_VERSION + 1) + dt[1:]
        self.assertRaises(DatagramVersionError, rec.input_data, alt_dt)

    def test_datagram_can_detect_crc_error(self):
        """
        Checks if a crc error is detected
        """
        rec = ReceiveDatagram()
        dt = encode_datagram(bytes("hello world!", 'ascii'), [23, 42])
        # alter crc
        alt_dt = dt[0:1] + struct.pack('>I', 0x00000000) + dt[5:]
        self.assertRaises(CRCMismatchError, rec.input_data, alt_dt)
