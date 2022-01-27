import unittest

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

import cvra_bootloader.can
from cvra_bootloader.utils import read_can_datagrams


class CANDatagramReaderTestCase(unittest.TestCase):
    """
    This testcase groups all tests related to reading a datagram from the bus.
    """

    def test_read_can_datagram(self):
        """
        Tests reading a complete CAN datagram from the bus.
        """
        data = "Hello world".encode("ascii")
        # Encapsulates it in a CAN datagram
        data = cvra_bootloader.can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = list(cvra_bootloader.can.datagram_to_frames(data, source=42))

        # Prepares a pseudo CAN adapter
        fdesc = Mock()
        fdesc.receive_frame.side_effect = frames

        reader = read_can_datagrams(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = next(reader)

        self.assertEqual(dt.decode("ascii"), "Hello world")
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)

    def test_drop_extended_frames(self):
        """
        Checks that we drop extended frames
        """
        data = "Hello world".encode("ascii")
        # Encapsulates it in a CAN datagram
        data = cvra_bootloader.can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = list(cvra_bootloader.can.datagram_to_frames(data, source=42))

        # Add an extended frame, with an annoying ID
        id = frames[0].id
        frames = [
            cvra_bootloader.can.Frame(extended=True, data=bytes([1, 2, 3]), id=id)
        ] + frames

        # Prepares a pseudo CAN adapter
        fdesc = Mock()
        fdesc.receive_frame.side_effect = frames

        reader = read_can_datagrams(fdesc)

        # Read a CAN datagram from that pseudofile
        dt, dst, src = next(reader)

        self.assertEqual(dt.decode("ascii"), "Hello world")
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)

    def test_read_can_interleaved_datagrams(self):
        """
        Tests reading two interleaved CAN datagrams together.
        """

        data = "Hello world".encode("ascii")

        # Encapsulates it in a CAN datagram
        data = cvra_bootloader.can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = [
            cvra_bootloader.can.datagram_to_frames(data, source=i) for i in range(2)
        ]

        # Interleave frames
        frames = [x for t in zip(*frames) for x in t]

        # Prepares a pseudo CAN adapter
        fdesc = Mock()
        fdesc.receive_frame.side_effect = frames

        decode = read_can_datagrams(fdesc)

        # Read the two datagrams
        _, _, src = next(decode)
        self.assertEqual(0, src)
        _, _, src = next(decode)
        self.assertEqual(1, src)

    def test_read_several_datagrams_from_src(self):
        """
        Checks if we can read several datagrams from the same source.
        """
        frames = []

        for i in range(2):
            # Encapsulates it in a CAN datagram
            dt = cvra_bootloader.can.encode_datagram(bytes(), destinations=[i])
            frames += list(cvra_bootloader.can.datagram_to_frames(dt, source=1))

        # Prepares a pseudo CAN adapter
        fdesc = Mock()
        fdesc.receive_frame.side_effect = frames

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
        # Prepares a pseudo CAN adapter that always timeout
        fdesc = Mock()
        fdesc.receive_frame.return_value = None

        reader = read_can_datagrams(fdesc)

        # Check that the timeout is returned
        self.assertIsNone(next(reader))

    def test_recover_from_timeout(self):
        """
        Tests reading a CAN datagram after a timeout.
        """
        data = "Hello world".encode("ascii")
        # Encapsulates it in a CAN datagram
        data = cvra_bootloader.can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = list(cvra_bootloader.can.datagram_to_frames(data, source=42))

        fdesc = Mock()

        # Insert a frame receive timeout
        fdesc.receive_frame.side_effect = frames[:1] + [None] + frames[1:]

        reader = read_can_datagrams(fdesc)

        # Check that the timeout is reported
        a = next(reader)
        self.assertIsNone(a)

        # Now try to read the real CAN datagram
        dt, dst, src = next(reader)

        self.assertEqual(dt.decode("ascii"), "Hello world")
        self.assertEqual(dst, [1])
        self.assertEqual(src, 42)
