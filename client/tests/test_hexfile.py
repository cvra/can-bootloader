import unittest
import os.path
import intel_hex

class IntelHexParserTestCase(unittest.TestCase):
    def test_can_parse_header(self):
        line = ":10002000000000000000000000000000C10300000C"
        line = intel_hex.parse_line(line)
        self.assertEqual(0x10, line.length)
        self.assertEqual(0x20, line.address)
        self.assertEqual(0, line.type)
        data = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xC1,0x03,0x00,0x00]
        self.assertEqual(line.data, data)

    def test_can_parse_type(self):
        line = ":00000001FF"
        line = intel_hex.parse_line(line)
        self.assertEqual(1, line.type)

class IntelHexToMemoryTestCase(unittest.TestCase):
    def test_can_do_single_line(self):
        """ Tests that converting a single line to binary works. """
        lines = [":10000000000000000000000000000000C10300000C"]
        memory, _ = intel_hex.to_memory(lines)
        expected = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xC1,0x03,0x00,0x00]
        self.assertEqual(expected, memory)

    def test_can_do_many_lines(self):
        """ Tests that we can convert many lines of IHex """
        lines = [":10000000000000000000000000000000C10300000C",":10001000000000000000000000000000cafebabe0C"]
        memory, _ = intel_hex.to_memory(lines)
        expected = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                    0xC1,0x03,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
                    0x00,0x00,0x00,0x00,0xca,0xfe,0xba,0xbe]
        self.assertEqual(expected, memory)

    def test_unused_memory_is_zero(self):
        """
        Tests that uninitialized memory is zero by writing data to some
        memory and checking that the whole region before is zero.
        """

        lines = [":10001000000000000000000000000000cafebabe0C"]
        memory, _ = intel_hex.to_memory(lines)
        self.assertEqual([0] * 0x10, memory[0:0x10])

    def test_other_types_are_ignored(self):
        """
        Checks that other line types than data do not write to the memory
        """
        lines = [":10001042000000000000000000000000cafebabe0C"]
        memory, _ = intel_hex.to_memory(lines)
        self.assertEqual([], memory)

    def test_exit_type_really_exits(self):
        """
        Checks that we don't parse lines after exit.
        """
        lines = [":00000001FF", ":10000000000000000000000000000000C10300000C"]
        memory, _ = intel_hex.to_memory(lines)
        self.assertEqual([], memory)

    def test_can_use_extended_records(self):
        lines = [":020000040001F2", ":10000000FF7F002049030008B1030008B90300087E"]
        memory, base = intel_hex.to_memory(lines)
        self.assertEqual(0x10000, base)
        self.assertEqual(memory[0x10000 - base], 0xff)

    @unittest.skip
    def test_can_open_huge_file(self):
        """
        Checks that we can open a real file and load it into memory.
        """
        path = os.path.join(os.path.dirname(__file__), "fixtures", "test.hex")
        with open(path) as f:
            memory, base = intel_hex.to_memory(f.readlines())

        self.assertEqual(base, 0)
        self.assertEqual(memory[1], 0x7f)
