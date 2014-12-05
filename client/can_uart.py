from collections import namedtuple
from msgpack import Packer


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

