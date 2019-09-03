import unittest
import io
import struct
from can.frame import Frame
from can.pcap import *
from socket import ntohl

# needed to expose private api
from can.pcap import _write_packet_header


class PCAPTest(unittest.TestCase):
    def test_write_file_header(self):
        f = io.BytesIO()
        write_header(f)

        header = struct.unpack('=LHHlLLL', f.getvalue())
        self.assertEqual(0xa1b2c3d4, header[0], 'bad magic header')
        self.assertEqual(2, header[1], 'bad version major')
        self.assertEqual(4, header[2], 'bad version minor')
        self.assertEqual(0, header[3], 'timezone is not GMT')
        # Sigfigs is not really used
        self.assertEqual(65535, header[5], 'bad snapshot length')
        self.assertEqual(227, header[6], 'network type is not socketcan')

    def test_write_packet_header(self):
        f = io.BytesIO()
        ts = 1000.5
        packet_length = 10
        _write_packet_header(f, ts, packet_length)

        header = struct.unpack('=4L', f.getvalue())

        self.assertEqual(1000, header[0], 'Invalid ts_sec')
        self.assertEqual(500000, header[1], 'Invalid ts_usec')
        self.assertEqual(10, header[2], 'Invalid incl_len')
        self.assertEqual(10, header[3], 'Invalid orig_len')

    def test_write_frame(self):
        f = io.BytesIO()
        ts = 1000.5
        data = "hello".encode()
        frame = Frame(0xcafe, data, extended=True, transmission_request=True)

        write_frame(f, ts, frame)

        fmt = PCAP_PKT_HDR_FMT + 'LBxxx' + '5s'
        data = struct.unpack(fmt, f.getvalue())

        # Check CAN ID (see http://www.tcpdump.org/linktypes/LINKTYPE_CAN_SOCKETCAN.html)
        expected_id = 0x40000000 + 0x80000000 + 0xcafe

        # The ID is stored in network byte order so we need to convert it to
        # host byte order before sending it
        self.assertEqual(data[4], ntohl(expected_id), 'wrong can id')
        self.assertEqual(data[5], 5, 'wrong frame length')
