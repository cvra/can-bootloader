from msgpack import Packer

class CommandType:
    JumpToMain = 1
    Write = 3

def encode_command(command_code, *arguments):
    """
    Encodes a command of the given type with given arguments.
    """
    p = Packer(use_bin_type=True)
    obj = list(arguments)
    return p.pack(command_code) +  p.pack(obj)

def encode_write_flash(data, adress, device_class):
    """
    Encodes the command to write the given data at the given adress in a
    messagepack byte object.
    """
    return encode_command(CommandType.Write, adress, device_class, data)

def encode_jump_to_main():
    """
    Encodes the command to jump to application using MessagePack.
    """
    return encode_command(CommandType.JumpToMain)
