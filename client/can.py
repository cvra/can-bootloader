import struct
from zlib import crc32

DATAGRAM_VERSION = 1

class Frame:
    """
    A single CAN frame.
    """
    def __init__(self, id=0, data=None, extended=False, transmission_request=False):
        if data is None:
            data = bytes()

        if len(data) > 8:
            raise ValueError

        self.id = id

        self.data = data
        self.transmission_request = transmission_request
        self.extended = extended



def encode_datagram(data, destinations):
    """
    Encodes the given data and destination list to form a complete datagram.
    This datagram can then be cut into CAN messages by datagram_to_frames.
    """

    version = struct.pack('B', DATAGRAM_VERSION)
    adresses = bytes([len(destinations)] + destinations)
    dt = struct.pack('>I', len(data)) + data
    crc = struct.pack('>I', crc32(adresses + dt))

    return version + crc + adresses + dt

def datagram_to_frames(datagram, source):
    """
    Transforms a raw datagram into CAN frames.
    """
    start_bit = (1 << 7)

    while len(datagram) > 8:
        data, datagram = datagram[:8], datagram[8:]

        yield Frame(id=start_bit + source, data=data)

        start_bit = 0

    yield Frame(id=start_bit + source, data=datagram)

class CRCMismatchError(RuntimeError):
    """
    Error raised when a datagram has an invalid CRC.
    """
    pass

class DatagramVersionError(RuntimeError):
    """
    Error raised when the datagram version is not supported.
    """
    pass

STATE_PROTOCOL_VERSION = 0
STATE_CRC = 1
STATE_DST_LEN = 2
STATE_DST = 3
STATE_DATA_LEN = 4
STATE_DATA = 5
STATE_TRAILING = 6
STATE_FINISHED = 7

class ReceiveDatagram:
    """
    CAN Datagram assembled from single CAN frames.
    """
    def __init__(self):
        self.state = STATE_PROTOCOL_VERSION
        self.data = b''
        self.crc = 0

    def input_data(self, data):
        self.data += data
        if self.state == STATE_PROTOCOL_VERSION:
            if len(self.data) >= 1:
                self.version = struct.unpack('B', self.data[:1])[0]
                self.data = self.data[1:]
                if self.version != DATAGRAM_VERSION:
                    raise DatagramVersionError
                self.state = STATE_CRC
        if self.state == STATE_CRC:
            if len(self.data) >= 4:
                self.rcv_crc = struct.unpack('>I', self.data[:4])[0]
                self.data = self.data[4:]
                self.state = STATE_DST_LEN
        if self.state == STATE_DST_LEN:
            if len(self.data) >= 1:
                self.crc = crc32(self.data[:1], self.crc)
                self.dest_len = struct.unpack('B', self.data[:1])[0]
                self.data = self.data[1:]
                self.state = STATE_DST
        if self.state == STATE_DST:
            if len(self.data) >= self.dest_len:
                self.crc = crc32(self.data[:self.dest_len], self.crc)
                self.dest = []
                for d in struct.iter_unpack('B',self.data[:self.dest_len]):
                    self.dest += d
                self.data = self.data[self.dest_len:]
                self.state = STATE_DATA_LEN
        if self.state == STATE_DATA_LEN:
            if len(self.data) >= 4:
                self.crc = crc32(self.data[:4], self.crc)
                self.data_len = struct.unpack('>I', self.data[:4])[0]
                self.data = self.data[4:]
                self.state = STATE_DATA
        if self.state == STATE_DATA:
            if len(self.data) >= self.data_len:
                self.crc = crc32(self.data[:self.data_len], self.crc)
                self.state = STATE_FINISHED
                if self.crc != self.rcv_crc:
                    raise CRCMismatchError
                return True
        return False
