import struct
from zlib import crc32
from .frame import *

DATAGRAM_VERSION = 1
START_OF_DATAGRAM_MASK = (1 << 7)

class VersionMismatchError(RuntimeError):
    """
    Error raised when attempting to decode a datagram with the wrong version.
    """
    pass

class CRCMismatchError(RuntimeError):
    """
    Error raised when attempting to decode a datagram with the wrong CRC.
    """
    pass

def is_start_of_datagram(frame):
    """
    Returns true if the given frame has the start of datagram marker.
    """
    return bool(frame.id & START_OF_DATAGRAM_MASK)

def encode_datagram(data, destinations):
    """
    Encodes the given data and destination list to form a complete datagram.
    This datagram can then be cut into CAN messages by datagram_to_frames.
    """

    version = struct.pack('B', DATAGRAM_VERSION)
    addresses = bytes([len(destinations)] + destinations)
    dt = struct.pack('>I', len(data)) + data
    crc = struct.pack('>I', crc32(addresses + dt))

    return version + crc + addresses + dt

def decode_datagram(data):
    """
    Decode the given datagram.
    Returns a tuple containing the data and the list of destination if the datagram is complete and valid.
    Returns None if the datagram is incomplete.

    Raise an exception if the datagram is invalid (wrong version or wrong CRC).
    """

    try:
        version, data = int(data[0]), data[1:]
        if version != DATAGRAM_VERSION:
            raise VersionMismatchError

        header_format = '>IB'
        header_len = struct.calcsize(header_format)
        header, data = data[0:header_len], data[header_len:]
        crc, dst_len = struct.unpack(header_format, header)

        # Decodes the destination list
        destination_format = '{}s'.format(dst_len)
        destinations, data = data[:dst_len], data[dst_len:]
        destinations = list(struct.unpack(destination_format, destinations)[0])

        data_len, data = data[:4], data[4:]
        data_len = struct.unpack('>I', data_len)[0]

        # If we did not receive all data yet
        if data_len != len(data):
            return None

        addresses = bytes([len(destinations)] + destinations)
        dt = struct.pack('>I', len(data)) + data

        if crc32(addresses + dt) != crc:
            raise CRCMismatchError

    except struct.error:
        # This means that we have not enough bytes to decode somewhere
        return None

    return data, destinations

def datagram_to_frames(datagram, source):
    """
    Transforms a raw datagram into CAN frames.
    """
    start_bit = START_OF_DATAGRAM_MASK

    while len(datagram) > 8:
        data, datagram = datagram[:8], datagram[8:]

        yield Frame(id=start_bit + source, data=data)

        start_bit = 0

    yield Frame(id=start_bit + source, data=datagram)

