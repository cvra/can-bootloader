from can_uart import *
import unittest
import msgpack

def encode_decode_frame(frame):
    """
    Returns a list containing the decoded fields from the encoded frame.
    """
    a = msgpack.Unpacker()
    a.feed(encode_frame(frame))

    return list(a)


class CanFrameEncodingTestCase(unittest.TestCase):
    """
    Testcase grouping all the functions relating to encoding CAN frames.
    """
    def test_frame_constructor(self):
        """
        Tests if we can instantiate a CAN Frame with default values.
        """
        frame = Frame(id=42)
        self.assertEqual(frame.id, 42)
        self.assertEqual(frame.data, bytes())
        self.assertFalse(frame.extended)
        self.assertFalse(frame.transmission_request)

    def test_frame_encode_extended(self):
        """
        Tests if encoding of the extended flag works.
        """
        frame = Frame(extended=True)
        msg = encode_decode_frame(frame)
        self.assertEqual(True, msg[0])

    def test_frame_encode_rtr(self):
        """
        Tests if encoding of the remote transmition request flag (RTR) works.
        """
        frame = Frame(transmission_request = True)
        msg = encode_decode_frame(frame)
        self.assertEqual(True, msg[1])

    def test_frame_encode_id(self):
        """
        Checks if encoding of Frame ID works correctly.
        """
        frame = Frame(id=42)
        msg = encode_decode_frame(frame)
        self.assertEqual(42, msg[2])

    def test_frame_encode_id(self):
        """
        Checks if encoding of data works properly.
        """
        frame = Frame(data=bytes([1,2,3]))
        msg = encode_decode_frame(frame)
        self.assertEqual(bytes([1,2,3]), msg[3])

    def test_frame_data_is_binary(self):
        """
        Checks if the encoded data is binary, not string.
        """

        frame = Frame(data=bytes([1,2,3]))
        data = encode_frame(frame)
        marker = 0xc4 # binary marker
        self.assertEqual(data[-4 - 1], marker)
        self.assertEqual(data[-4], len(frame.data))
