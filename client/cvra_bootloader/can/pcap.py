import struct

# See https://wiki.wireshark.org/Development/LibpcapFileFormat
PCAP_HDR_FORMAT = '=LHHlLLL'
PCAP_PKT_HDR_FMT = '=4L'
SOCKETCAN_HDR_FMT = '!LBxxx'


def write_header(outfile):
    magic = 0xa1b2c3d4
    ver_maj, ver_min = 2, 4
    thiszone = 0
    sigfigs = 0
    snaplen = 65535
    network = 227  # SocketCAN

    hdr = struct.pack(PCAP_HDR_FORMAT, magic, ver_maj, ver_min, thiszone,
                      sigfigs, snaplen, network)
    outfile.write(hdr)


def _write_packet_header(outfile, timestamp, packet_length):
    #ts_sec, ts_usec = int(timestamp), int(1000000 *
    ts_sec = int(timestamp)
    ts_usec = int(1000000 * (timestamp - ts_sec))

    hdr = struct.pack(PCAP_PKT_HDR_FMT, ts_sec, ts_usec, packet_length,
                      packet_length)
    outfile.write(hdr)


def write_frame(outfile, timestamp, frame):
    _write_packet_header(outfile, timestamp, frame.data_length + 8)

    # Check http://www.tcpdump.org/linktypes/LINKTYPE_CAN_SOCKETCAN.html
    id_with_flags = frame.id

    if frame.extended:
        id_with_flags |= 0x80000000

    if frame.transmission_request:
        id_with_flags |= 0x40000000

    data = struct.pack(SOCKETCAN_HDR_FMT, id_with_flags,
                       frame.data_length) + frame.data
    outfile.write(data)
