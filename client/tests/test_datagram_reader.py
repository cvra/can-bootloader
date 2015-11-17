import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import can
import can_bridge
import serial_datagrams

from can.adapters import SerialCANBridgeConnection
from utils import read_can_datagrams
from io import BytesIO


class CANDatagramReaderTestCase(unittest.TestCase):
    """
    This testcase groups all tests related to reading a datagram from the bus.
    """
    def test_read_can_datagram(self):
        """
        Tests reading a complete CAN datagram from the bus.
        """
        data = 'Hello world'.encode('ascii')
        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = can.datagram_to_frames(data, source=42)

        # Serializes CAN frames for the bridge
        frames = [can_bridge.frame.encode(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = SerialCANBridgeConnection(BytesIO(frames))

        reader = read_can_datagrams(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = next(reader)

        self.assertEqual(dt.decode('ascii'), 'Hello world')
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)

    def test_drop_extended_frames(self):
        """
        Checks that we drop extended frames
        """
        data = 'Hello world'.encode('ascii')
        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = list(can.datagram_to_frames(data, source=42))

        # Add an extended frame, with an annoying ID
        id = frames[0].id
        frames = [can_bridge.frame.Frame(extended=True, data=bytes([1, 2, 3]), id=id)] + frames

        # Serializes CAN frames for the bridge
        frames = [can_bridge.frame.encode(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = SerialCANBridgeConnection(BytesIO(frames))

        reader = read_can_datagrams(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = next(reader)

        self.assertEqual(dt.decode('ascii'), 'Hello world')
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)



    def test_read_can_interleaved_datagrams(self):
        """
        Tests reading two interleaved CAN datagrams together.
        """

        data = 'Hello world'.encode('ascii')
        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = [can.datagram_to_frames(data, source=i) for i in range(2)]

        # Interleave frames
        frames = [x for t in zip(*frames) for x in t]

        # Serializes CAN frames for the bridge
        frames = [can_bridge.frame.encode(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)

        # Put all data in a pseudofile
        fdesc = SerialCANBridgeConnection(BytesIO(frames))

        decode = read_can_datagrams(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = next(decode)

    def test_read_several_datagrams_from_src(self):
        """
        Checks if we can read several datagrams from the same source.
        """
        data = bytes()

        for i in range(2):
            # Encapsulates it in a CAN datagram
            dt = can.encode_datagram(bytes(), destinations=[i])
            frames = can.datagram_to_frames(dt, source=1)
            frames = [can_bridge.frame.encode(f) for f in frames]
            frames = bytes(c for i in [serial_datagrams.datagram_encode(f) for f in frames] for c in i)
            data += frames

        fdesc = SerialCANBridgeConnection(BytesIO(data))
        decode = read_can_datagrams(fdesc)

        # Read a CAN datagram from that pseudofile
        _, dst, _ = next(decode)
        self.assertEqual([0], dst)

        _, dst, _ = next(decode)
        self.assertEqual([1], dst)



    def test_read_can_datagram_timeout(self):
        """
        Tests reading a datagram with a timeout (read_datagram returns None).
        """
        data = 'Hello world'.encode('ascii')

        reader = read_can_datagrams(SerialCANBridgeConnection(None))

        with patch('serial_datagrams.read_datagram') as read:
            read.return_value = None
            a = next(reader)

        self.assertIsNone(a)

