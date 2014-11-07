from growing_list import GrowingList
from collections import namedtuple

IHexLine = namedtuple("IHexLine", ['length', 'adress', 'type', 'data'])

class RecordType:
    Data = 0
    End = 1
    ExtendedAdressMode = 4

def ihex_parse_line(line):
    length = int(line[1:3], 16)
    adress = int(line[3:7], 16)
    type = int(line[7:9])

    data = []
    data_part = line[9:-2]
    for i in range(0, len(data_part), 2):
        data.append(int(data_part[i:i+2], 16))

    return IHexLine(length=length, adress=adress, type=type, data=bytes(data))

def ihex_to_memory(lines):
    """
    Transforms a list of lines into a binary memory representation.
    """
    memory = GrowingList(default_value=0)
    base_adress = 0
    start_adress = 0

    for l in lines:
        l = ihex_parse_line(l)

        if l.type == RecordType.Data:
            for i in range(l.length):
                memory[base_adress - start_adress + l.adress + i] = l.data[i]

        elif l.type == RecordType.ExtendedAdressMode:
            base_adress  = l.data[0] << 8
            base_adress += l.data[1]
            base_adress <<= 16

            if start_adress == 0:
                start_adress = base_adress

        elif l.type == RecordType.End:
            break

    return memory, start_adress

