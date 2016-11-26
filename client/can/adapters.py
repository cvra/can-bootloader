import can
import socket
import struct
import serial
from queue import Queue
import threading

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

        return can.Frame(id=can_id, data=data[:can_dlc])

class SerialCANConnection:
    """
    Implements the slcan API.
    """

    MIN_MSG_LEN = len('t1230')

    def __init__(self, port):
        self.port = port

        self.rx_queue = Queue()
        t = threading.Thread(target=self.spin)
        t.daemon = True
        t.start()

        self.send_command('S8'); # bitrate 1Mbit
        self.send_command('O'); # open device
        port.reset_input_buffer()

    def spin(self):
        part = ''
        while True:
            part += self.port.read(100).decode('ascii')

            if part.startswith('\r'):
                part.lstrip('\r')

            if '\r' not in part:
                continue

            data = part.split('\r')
            data, part = data[:-1], data[-1]

            for frame in data:
                if frame is None:
                    continue
                frame = self.decode_frame(frame)
                if frame:
                    self.rx_queue.put(frame)

    def send_command(self, cmd):
        cmd += '\r'
        cmd = cmd.encode('ascii')
        self.port.write(cmd)

    def decode_frame(self, msg):
        if len(msg) < self.MIN_MSG_LEN:
            return None

        cmd, msg = msg[0], msg[1:]
        if cmd == 'T':
            extended = True
            id_len = 8
        elif cmd == 't':
            extended = False
            id_len = 3
        else:
            return None

        if len(msg) < id_len + 1:
            return None
        can_id = int(msg[0:id_len], 16)
        msg = msg[id_len:]
        data_len = int(msg[0])
        msg = msg[1:]
        if len(msg) < 2 * data_len:
            return None
        data = [int(msg[i:i+2], 16) for i in range(0, 2 * data_len, 2)]

        return can.Frame(id=can_id, data=bytearray(data), data_length=data_len, extended=extended)

    def encode_frame(self, frame):
        if frame.extended:
            cmd = 'T'
            can_id = '{:08x}'.format(frame.id)
        else:
            cmd = 't'
            can_id = '{:03x}'.format(frame.id)

        length = '{:x}'.format(frame.data_length)

        data = ''
        for b in frame.data:
            data += '{:02x}'.format(b)
        return cmd + can_id + length + data

    def send_frame(self, frame):
        cmd = self.encode_frame(frame)
        self.send_command(cmd)

    def receive_frame(self):
        try:
            return self.rx_queue.get(True, 1) # block with timeout 1 sec
        except:
            return None
