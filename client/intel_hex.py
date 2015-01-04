from growing_list import GrowingList
from collections import namedtuple

IHexLine = namedtuple("IHexLine", ['length', 'address', 'type', 'data'])

class RecordType:
    Data = 0
    End = 1
    ExtendedAddressMode = 4

def parse_line(line):
    length = int(line[1:3], 16)
    address = int(line[3:7], 16)
    type = int(line[7:9])

    data = []
    data_part = line[9:-2]
    for i in range(0, len(data_part), 2):
        data.append(int(data_part[i:i+2], 16))

    return IHexLine(length=length, address=address, type=type, data=data)

def to_memory(lines):
    """
    Transforms a list of lines into a binary memory representation.
    """
    memory = GrowingList(default_value=0)
    base_address = 0
    start_address = 0

    for l in lines:
        l = parse_line(l)

        if l.type == RecordType.Data:
            for i in range(l.length):
                memory[base_address - start_address + l.address + i] = l.data[i]

        elif l.type == RecordType.ExtendedAddressMode:
            base_address  = l.data[0] << 8
            base_address += l.data[1]
            base_address <<= 16

            if start_address == 0:
                start_address = base_address

        elif l.type == RecordType.End:
            break

    return memory, start_address

