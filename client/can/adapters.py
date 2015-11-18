import serial_datagrams
import can_bridge
import can_bridge.commands
import socket
import struct

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

class SocketCANConnection:
    # See <linux/can.h> for format
    CAN_FRAME_FMT = "=IB3x8s"
    CAN_FRAME_SIZE = struct.calcsize(CAN_FRAME_FMT)


    def __init__(self, interface):
        """
        Initiates a CAN connection on the given interface (e.g. 'can0').
        """
        # Creates a raw CAN connection and binds it to the given interface.
        self.socket = socket.socket(socket.AF_CAN,
                                    socket.SOCK_RAW,
                                    socket.CAN_RAW)

        self.socket.bind((interface, ))

    def send_frame(self, frame):
        data = frame.data.ljust(8, b'\x00')
        data = struct.pack(self.CAN_FRAME_FMT,
                           frame.id,
                           len(frame.data),
                           data)

        self.socket.send(data)

    def receive_frame(self):
        frame, _ = self.socket.recvfrom(self.CAN_FRAME_SIZE)
        can_id, can_dlc, data = struct.unpack(self.CAN_FRAME_FMT, frame)

        return can_bridge.frame.Frame(id=can_id, data=data[:can_dlc])

