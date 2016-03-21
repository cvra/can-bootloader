from msgpack import Packer

COMMAND_SET_VERSION = 2

class CommandType:
    JumpToMain = 1
    CRCReginon = 2
    Erase = 3
    Write = 4
    Ping = 5
    Read = 6
    UpdateConfig = 7
    SaveConfig = 8
    ReadConfig = 9

def encode_command(command_code, *arguments):
    """
    Encodes a command of the given type with given arguments.
    """
    p = Packer(use_bin_type=True)
    obj = list(arguments)
    return p.pack(COMMAND_SET_VERSION) + p.pack(command_code) +  p.pack(obj)

def encode_crc_region(address, length):
    """
    Encodes the command to request the CRC of a region in flash.
    """
    return encode_command(CommandType.CRCReginon, address, length)

def encode_erase_flash_page(address, device_class):
    """
    Encodes the command to erase the flash page at given address.
    """
    return encode_command(CommandType.Erase, address, device_class)

def encode_write_flash(data, address, device_class):
    """
    Encodes the command to write the given data at the given address in a
    messagepack byte object.
    """
    return encode_command(CommandType.Write, address, device_class, data)

def encode_read_flash(aderess, length):
    """
    Encodes the command to read the flash at given address.
    """
    return encode_command(CommandType.Read, address, length)

def encode_update_config(data):
    """
    Encodes the command to update the config from given MessagePack data.
    """
    return encode_command(CommandType.UpdateConfig, data)

def encode_save_config():
    """
    Encodes the command to save the config to flash.
    """
    return encode_command(CommandType.SaveConfig)

def encode_jump_to_main():
    """
    Encodes the command to jump to application using MessagePack.
    """
    return encode_command(CommandType.JumpToMain)

def encode_read_config():
    """
    Encodes the read config command.
    """
    return encode_command(CommandType.ReadConfig)

def encode_ping():
    """
    Encodes a ping command.
    """
    return encode_command(CommandType.Ping)
