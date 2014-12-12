import struct
from zlib import crc32

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

    adresses = bytes([len(destinations)] + destinations)
    dt = struct.pack('>I', len(data)) + data
    crc = struct.pack('>I', crc32(adresses + dt))

    return crc + adresses + dt

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

