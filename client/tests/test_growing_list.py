import unittest
from growing_list import *

class GrowingListTestCase(unittest.TestCase):
    def test_has_list_properties(self):
        """
        Tests that GrowingList still works as basic lists for
        """
        a = GrowingList()
        a.append(2)
        a.append(3)
        self.assertEqual([2, 3], a)

    def test_none_is_default_value(self):
        a = GrowingList()
        a[0] = 2
        a[2] = 3
        self.assertEqual([2, None, 3], a)

    def test_can_change_default_value(self):
        a = GrowingList(default_value=0)
        a[0] = 2
        a[2] = 3
        self.assertEqual([2, 0, 3], a)

    def test_can_be_used_as_iterator(self):
        a = GrowingList()
        a[1] = 2
        a = iter(a)
        self.assertEqual(None, next(a))
        self.assertEqual(2, next(a))

        with self.assertRaises(StopIteration):
            next(a)
