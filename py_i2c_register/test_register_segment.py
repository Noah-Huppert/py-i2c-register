import unittest
from py_i2c_register.register_segment import RegisterSegment

class TestRegisterSegmentToBits(unittest.TestCase):
    def test_pos_in_range(self):
        self.assertEqual(RegisterSegment.to_bits(12, 8), [0, 0, 0, 0, 1, 1, 0, 0])

    def test_pos_out_range(self):
        with self.assertRaises(ValueError):
            RegisterSegment.to_bits(300, 8)

    def test_neg(self):
        with self.assertRaises(ValueError):
            RegisterSegment.to_bits(-2, 8)

class TestRegisterSegmentToInt(unittest.TestCase):
    def test_number(self):
        self.assertEqual(RegisterSegment.to_int([0, 0, 0, 0, 1, 1, 0, 0]), 12)

#class TestRegisterSegmentToTwosCompInt(unittest.TestCase):
