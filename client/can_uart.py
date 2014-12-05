from collections import namedtuple
from msgpack import Packer, Unpacker


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

def encode_frame(frame):
    """
    Encodes the given frame to raw messagepack bytes.
    """
    packer = Packer(use_bin_type=True)
    data = packer.pack(frame.extended)
    data = data + packer.pack(frame.transmission_request)
    data = data + packer.pack(frame.id)
    data += packer.pack(frame.data)

    return data

def decode_frame(data):
    """
    Decodes the given messagepack bytes to a Frame object.
    """
    unpacker = Unpacker()
    result = Frame()

    unpacker.feed(data)

    result.extended = unpacker.unpack()
    result.transmission_request = unpacker.unpack()
    result.id = unpacker.unpack()
    result.data = unpacker.unpack()

    return result

