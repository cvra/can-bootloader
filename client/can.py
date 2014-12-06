import struct
from zlib import crc32

class Frame:
    """
    A single CAN frame.
    """
    def __init__(self, id=0, data=None, extended=False, transmission_request=False):
        if data is None:
            data = bytes()
        self.id = id
        self.data = data
        self.transmission_request = transmission_request
        self.extended = extended



def encode_datagram(destinations, data):

    adresses = bytes([len(destinations)] + destinations)
    dt = struct.pack('>I', len(data)) + data

    crc = struct.pack('>I', crc32(adresses + dt))

    return crc + adresses + dt
