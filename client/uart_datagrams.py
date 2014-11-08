import struct
from zlib import crc32

END = b'\xC0'
ESC = b'\xDB'
ESC_END = b'\xDC'
ESC_ESC = b'\xDD'

def datagram_encode(data):
    """
    Encodes the given datagram (bytes object) by adding a CRC at the end then an end marker.
    It also escapes the end marker correctly.
    """
    data = data + struct.pack('>I', crc32(data))
    data = data.replace(ESC, ESC + ESC_ESC)
    data = data.replace(END, ESC + ESC_END)
    return data + END
