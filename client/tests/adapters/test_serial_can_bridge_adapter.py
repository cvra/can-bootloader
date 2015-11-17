from unittest import TestCase
try:
    from unittest.mock import *
except ImportError:
    from mock import *

import can
import can_bridge
import serial_datagrams

from can.adapters import SerialCANBridgeConnection
from io import BytesIO

class SerialCANBridgeConnectionTestCase(TestCase):
    def test_write_can_frame(self):
        frame = can.Frame()
        bridge_frame = can_bridge.commands.encode_frame_write(frame)

        bridge_datagram = serial_datagrams.datagram_encode(bridge_frame)

        fdesc = Mock()
        conn = SerialCANBridgeConnection(fdesc)

        conn.send_frame(frame)

        fdesc.write.assert_any_call(bridge_datagram)
        fdesc.flush.assert_any_call()

    def test_receive_can_frame(self):
        frame = can.Frame(id=42, data=bytes(range(3)))
        encoded_frame = can_bridge.frame.encode(frame)
        encoded_frame = serial_datagrams.datagram_encode(encoded_frame)

        # Put all data in a pseudofile
        conn = SerialCANBridgeConnection(BytesIO(encoded_frame))

        f = conn.receive_frame()
        self.assertEqual(frame, f)
