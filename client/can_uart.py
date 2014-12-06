import msgpack
from can import Frame


def encode_frame(frame):
    """
    Encodes the given frame to raw messagepack bytes.
    """
    packer = msgpack.Packer(use_bin_type=True)
    data = packer.pack(frame.extended)
    data = data + packer.pack(frame.transmission_request)
    data = data + packer.pack(frame.id)
    data += packer.pack(frame.data)

    return data

def decode_frame(data):
    """
    Decodes the given messagepack bytes to a Frame object.
    """
    unpacker = msgpack.Unpacker()
    result = Frame()

    unpacker.feed(data)

    result.extended = unpacker.unpack()
    result.transmission_request = unpacker.unpack()
    result.id = unpacker.unpack()
    result.data = unpacker.unpack()

    return result

