import unittest

from mock import patch
from py_i2c_register.register_segment import RegisterSegment

class TestRegisterSegmentToBits(unittest.TestCase):
    def test_pos_in_range(self):
        self.assertEqual(RegisterSegment.to_bits(12, 8), [0, 0, 1, 1, 0, 0, 0, 0])

    def test_pos_out_range(self):
        with self.assertRaises(ValueError):
            RegisterSegment.to_bits(300, 8)

    def test_neg(self):
        with self.assertRaises(ValueError):
            RegisterSegment.to_bits(-2, 8)

class TestRegisterSegmentToInt(unittest.TestCase):
    def test_number(self):
        self.assertEqual(RegisterSegment.to_int([0, 0, 1, 1, 0, 0, 0, 0]), 12)

class TestRegisterSegmentToTwosCompInt(unittest.TestCase):
    def test_neg_number(self):
        self.assertEqual(RegisterSegment.to_twos_comp_int([0, 1, 0, 1, 1, 1, 1, 1]), -6)

    def test_pos_number(self):
        self.assertEqual(RegisterSegment.to_twos_comp_int([0, 0, 1, 1, 0, 0, 0, 0]), 12)

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
        self.assertEqual(RegisterSegment.to_padded_byte_arr([0, 0, 1, 1, 0, 0, 0, 0]), [12])

    def test_one_byte_partial_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([1, 1, 1, 1]), [15])

    def test_two_bytes_partial_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1]), [85, 10])

    def test_two_bytes_perfect_fit(self):
        self.assertEqual(RegisterSegment.to_padded_byte_arr([0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0]), [170, 85])

class TestRegisterSegmentInit(unittest.TestCase):
    def test_perfect(self):
        seg = RegisterSegment("NAME", 0, 7, [0] * 8)
        self.assertEqual(seg.name, "NAME")
        self.assertEqual(seg.lsb_i, 0)
        self.assertEqual(seg.msb_i, 7)
        self.assertEqual(seg.bits, [0] * 8)

    def test_lsb_higher_than_msb(self):
        with self.assertRaises(ValueError):
            seg = RegisterSegment("NAME", 7, 0, [0] * 8)

    def test_provided_bits_too_small(self):
        with self.assertRaises(IndexError):
            seg = RegisterSegment("NAME", 0, 7, [0])

class TestRegisterSegmentProxyMethods(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.bits = [1, 0, 1, 0, 1, 0, 1, 0]

    def setUp(self):
        self.seg = RegisterSegment("NAME", 0, 7, self.bits)

    @patch("py_i2c_register.register_segment.RegisterSegment")
    def test_bytes_to_int(self, RS):
        self.seg.bytes_to_int()
        RS.to_int.assert_called_once_with(self.bits)

    @patch("py_i2c_register.register_segment.RegisterSegment")
    def test_bytes_to_twos_comp_int(self, RS):
        self.seg.bytes_to_twos_comp_int()
        RS.to_twos_comp_int.assert_called_once_with(self.bits)

class TestRegisterSegmentUpdateBits(unittest.TestCase):
    def test_perfect(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        seg.update_bits([213, 170])
        self.assertEqual(seg.bits, [1, 0, 1])

    def test_in_second_byte(self):
        seg = RegisterSegment("NAME", 9, 11, [0] * 3)
        seg.update_bits([213, 170])
        self.assertEqual(seg.bits, [1, 0, 1])

    def test_not_enough_bits(self):
        seg = RegisterSegment("NAME", 9, 11, [0] * 3)
        with self.assertRaises(KeyError):
            seg.update_bits([240])

class TestRegisterSegmentSetBits(unittest.TestCase):
    def test_perfect(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        seg.set_bits([1, 1, 0])
        self.assertEqual(seg.bits, [1, 1, 0])

    def test_too_many_bits(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        with self.assertRaises(IndexError):
            seg.set_bits([0, 1, 0, 1])

    def test_too_few_bits(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        with self.assertRaises(IndexError):
            seg.set_bits([0])

    def test_bit_value_err(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        with self.assertRaises(ValueError):
            seg.set_bits([1, 2, 3])

class TestRegisterSegmentGenericMethods(unittest.TestCase):
    def test_str(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        self.assertEqual(str(seg), "RegisterSegment<name=NAME, lsb_i=0, msb_i=2, bits=[0, 0, 0]>")

    def test_len(self):
        seg = RegisterSegment("NAME", 0, 2, [0] * 3)
        self.assertEqual(len(seg), 3)
