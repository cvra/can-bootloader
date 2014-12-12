from msgpack import Packer

class CommandType:
    JumpToMain = 1
    Write = 3

def encode_write_flash(data, adress, device_class):
    """
    Encodes the command to write the given data at the given adress in a
    messagepack byte object.
    """
    p = Packer(use_bin_type=True)
    obj = [adress, device_class, data]
    return p.pack(CommandType.Write) +  p.pack(obj)

def encode_jump_to_main():
    """
    Encodes the command to jump to application using MessagePack.
    """
    p = Packer(use_bin_type=True)
    return p.pack(CommandType.JumpToMain)
