import can, commands, serial_datagrams, can_bridge
import unittest

class IntegrationTesting(unittest.TestCase):
    def test_encoding_whole_stack(self):
        """
        Checks that the whole stack needed to encode a write command still works.
        """

        data = 'Hello, world!'.encode('ascii')

        # Generates the command
        data = commands.encode_write_flash(data, address=0x00, device_class="dummy")

        # Encapsulates it in a CAN datagram
        data = can.encode_datagram(data, destinations=[1])

        # Slice the datagram in frames
        frames = can.datagram_to_frames(data, source=0)

        # Serializes CAN frames for the bridge
        frames = [can_bridge.encode_frame(f) for f in frames]

        # Packs each frame in a serial datagram
        frames = [serial_datagrams.datagram_encode(f) for f in frames]

        # Flattens the list of UART datagram frames to a stream of byte
        data = [c for f in frames for c in f]

        # Pseudo-check that encoding went well
        self.assertEqual(len(data), 88)

