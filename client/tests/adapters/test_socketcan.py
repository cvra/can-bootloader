from unittest import TestCase

try:
    from unittest.mock import *
except ImportError:
    from mock import *


import socket
import struct
from cvra_bootloader.can.adapters import SocketCANConnection
from cvra_bootloader.can import Frame

# SocketCAN compatibility shims for OSX
try:
    from socket import AF_CAN
except ImportError:
    socket.AF_CAN = "AF_CAN"
    socket.CAN_RAW = "CAN_RAW"


@patch("socket.socket")
class SocketCANTestCase(TestCase):
    def test_can_open_connection(self, socket_create):
        """
        Checks that we can correctly open a connection.
        """
        SocketCANConnection("vcan0")

        socket_create.assert_any_call(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)

        socket_create.return_value.bind.assert_any_call(("vcan0",))
        socket_create.return_value.settimeout.assert_any_call(ANY)
        socket_create.return_value.setsockopt.assert_any_call(
            socket.SOL_SOCKET, socket.SO_SNDBUF, 4096
        )

    def test_can_send_frame(self, socket_create):
        s = SocketCANConnection("vcan0")
        s.socket = Mock()

        frame = Frame(id=42, data=bytes((0xDE, 0xAD, 0xBE, 0xEF)))

        # See <linux/can.h> for format
        # Data field must be zero padded
        can_frame = struct.pack(
            "=IB3x8s", 42, 4, bytes((0xDE, 0xAD, 0xBE, 0xEF, 0x0, 0x0, 0x0, 0x0))
        )

        s.send_frame(frame)

        s.socket.send.assert_any_call(can_frame)

    def test_receive_frame(self, socket_create):
        s = SocketCANConnection("vcan0")
        s.socket = Mock()

        expected_frame = Frame(id=42, data=bytes((0xDE, 0xAD, 0xBE, 0xEF)))

        can_frame = struct.pack(
            "=IB3x8s", 42, 4, bytes((0xDE, 0xAD, 0xBE, 0xEF, 0x0, 0x0, 0x0, 0x0))
        )

        s.socket.recvfrom.return_value = (can_frame, ("vcan0"))

        actual_frame = s.receive_frame()

        self.assertEqual(expected_frame, actual_frame)

    def test_receive_frame_timeout(self, socket_create):
        s = SocketCANConnection("vcan0")
        s.socket = Mock()
        s.socket.recvfrom.side_effect = [socket.timeout]

        s.receive_frame()
