import unittest
from cvra_bootloader.page import *


class PaginationTestCase(unittest.TestCase):
    def test_smaller_than_page_is_yielded(self):
        """
        Tests that a page smaller than the page size is yielded entierly.
        """
        b = bytes([1])
        p = slice_into_pages(b, page_size=4)
        self.assertEqual(next(p), b)

    def test_can_cut_into_subpages(self):
        """
        Tests that a page is split into subpages.
        """
        b = bytes(range(17))
        p = slice_into_pages(b, page_size=4)

        self.assertEqual(next(p), bytes(range(0, 4)))
        self.assertEqual(next(p), bytes(range(4, 8)))
        self.assertEqual(next(p), bytes(range(8, 12)))
        self.assertEqual(next(p), bytes(range(12, 16)))
        self.assertEqual(next(p), bytes([16]))
