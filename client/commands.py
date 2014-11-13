from msgpack import Packer

class CommandType:
    Write = 3

def encode_write_flash(adress, data, device_class):
    """
    Encodes the command to write the given data at the given adress in a
    messagepack byte object.
    """
    p = Packer(use_bin_type=True)
    obj = [adress, device_class, data]
    return p.pack(CommandType.Write) +  p.pack(obj)
