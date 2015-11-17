import serial_datagrams
import can_bridge
import can_bridge.commands

class SerialCANBridgeConnection:
    """
    Implements the CAN API for serial bridge.
    """
    def __init__(self, fd):
        self.fd = fd

    def send_frame(self, frame):
        bridge_frame = can_bridge.commands.encode_frame_write(frame)
        datagram = serial_datagrams.datagram_encode(bridge_frame)
        self.fd.write(datagram)
        self.fd.flush()

    def receive_frame(self):
        frame = serial_datagrams.read_datagram(self.fd)
        if frame is None:  # Timeout, retry
            return None

        return can_bridge.frame.decode(frame)
