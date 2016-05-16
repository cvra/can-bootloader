import can
import socket
import struct
import serial
from queue import Queue

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
        self.socket.settimeout(1.)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)

    def send_frame(self, frame):
        data = frame.data.ljust(8, b'\x00')
        data = struct.pack(self.CAN_FRAME_FMT,
                           frame.id,
                           len(frame.data),
                           data)

        self.socket.send(data)

    def receive_frame(self):
        try:
            frame, _ = self.socket.recvfrom(self.CAN_FRAME_SIZE)
        except socket.timeout:
            return None
        can_id, can_dlc, data = struct.unpack(self.CAN_FRAME_FMT, frame)

        # Extract extended frame flag
        extended = bool(can_id & (1 << 31))

        # Extract can ID (29 LSB)
        can_id = can_id & ((1 << 30) - 1)

        return can.Frame(id=can_id, data=data[:can_dlc])

class CVRACANDongleConnection:
    """
    Implements the CAN API for the CVRA CAN dongle.
    """
    def __init__(self, port, baudrate=115200, timeout=None):
        import cvra_can
        self.cvra_can = cvra_can
        from datagrammessages import SerialConnection

        self.conn = SerialConnection(port)
        self.conn.set_msg_handler('rx', lambda msg: self.rx_handler(msg))
        self.conn.set_msg_handler('drop', self.drop_handler)

        id_filter = [int(self.cvra_can.Frame.ID(0, extended=0)),
                     self.cvra_can.Frame.ID.mask(0, extended=1)]
        if not self.conn.service_call('filter', id_filter):
            print('filter configuration error')
            sys.exit(1)
        self.conn.service_call('silent', False)
        self.conn.service_call('loop back', False)
        self.conn.service_call('bit rate', 1000000)
        self.rx_queue = Queue()

    def rx_handler(self, msg):
        rec = self.cvra_can.Frame.decode(msg[0])
        if rec.can_id.extended:
            return
        frame = can.Frame(id=rec.can_id.value,
                                 data=rec.data,
                                 extended=rec.can_id.extended,
                                 transmission_request=rec.can_id.remote,
                                 data_length=len(rec.data))
        self.rx_queue.put(frame)

    def drop_handler(self, msg):
        # non fatal error
        # print a warning?
        pass

    def send_frame(self, frame):
        ident = self.cvra_can.Frame.ID(value=frame.id,
                                  extended=frame.extended,
                                  remote=frame.transmission_request)
        if frame.transmission_request:
            data = frame.data_length * b'0'
        else:
            data = frame.data
        frame = self.cvra_can.Frame(can_id=ident, data=data).encode()
        self.conn.service_call('tx', [frame])

    def receive_frame(self):
        try:
            return self.rx_queue.get(True, 1) # block with timeout 1 sec
        except:
            return None
