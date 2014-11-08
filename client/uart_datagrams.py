import struct
from zlib import crc32

class CRCMismatchError(RuntimeError):
    """
    Error raised when a packet has an invalid CRC.
    """
    pass

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

def datagram_decode(data):
    """
    Decodes a datagram. Exact inverse of datagram_encode()
    """
    data = data[:-1] # remove end marker
    data = data.replace(ESC + ESC_ESC, ESC)
    data = data.replace(ESC + ESC_END, END)

    expected_crc = struct.unpack('>I', data[-4:])[0]
    actual_crc = crc32(data[:-4])

    if expected_crc != actual_crc:
        raise CRCMismatchError

    return data[:-4]
