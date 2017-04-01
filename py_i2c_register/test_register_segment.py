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

class TestRegisterSegmentToTwosCompInt(unittest.TestCase):
    def test_number(self):
        self.assertEqual(RegisterSegment.to_two_comp_int([1, 1, 1, 1, 1, 0, 1, 0]), -6)

class TestRegisterSegmentNumBytesForBits(unittest.TestCase):
    def test_lower_range(self):
        self.assertEqual(RegisterSegment.num_bytes_for_bits(2), 1)

    def test_upper_range(self):
        self.assertEqual(RegisterSegment.num_bytes_for_bits(7), 1)

    def test_simple_overflow(self):
        self.assertEqual(RegisterSegment.num_bytes_for_bits(9), 2)

    def test_zero(self):
        self.assertEqual(RegisterSegment.num_bytes_for_bits(0), 0)

class TestRegisterSegmentToPaddedByteArr(unittest.TestCase):
    def test_empty_bits(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([]), [])

    def test_one_byte_perfect_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([0, 0, 0, 0, 1, 1, 0, 0]), [12])

    def test_one_byte_partial_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([1, 1, 1, 1]), [240])

    def test_two_bytes_partial_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1]), [170, 80])

    def test_two_bytes_perfect_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0]), [85, 170])

