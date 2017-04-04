import unittest

from mock import MagicMock
from mock import patch

from py_i2c_register.register import Register
from py_i2c_register.register_segment import RegisterSegment

class TestRegisterInit(unittest.TestCase):
    def test_perfect(self):
        reg = Register("NAME", 1, 2, "WRITEMODE", {"key": "value"})

        self.assertEqual(reg.name, "NAME")
        self.assertEqual(reg.dev_addr, 1)
        self.assertEqual(reg.reg_addr, 2)
        self.assertEqual(reg.op_mode, "WRITEMODE")
        self.assertEqual(reg.segments, {"key": "value"})

class TestRegisterGet(unittest.TestCase):
    def setUp(self):
        self.reg = Register("NAME", 1, 2, "WRITEMODE", {})
        self.reg.add("SEG_NAME", 0, 2, [0] * 3)

    def test_perfect(self):
        ret = self.reg.get("SEG_NAME")
        self.assertEqual(ret.name, "SEG_NAME")
        self.assertEqual(ret.lsb_i, 0)
        self.assertEqual(ret.msb_i, 2)
        self.assertEqual(ret.bits, [0] * 3)

    def test_non_existant(self):
        with self.assertRaises(KeyError):
            self.reg.get("DOES_NOT_EXIST")

class TestRegisterProxyMethods(unittest.TestCase):
    def setUp(self):
        self.reg = Register("NAME", 1, 2, "WRITEMODE", {})
        self.reg.add("SEG_NAME", 0, 2, [0] * 3)

    def test_set_bits(self):
        self.reg.get("SEG_NAME").set_bits = MagicMock()
        self.reg.set_bits("SEG_NAME", [1, 0, 1])
        self.reg.get("SEG_NAME").set_bits.called_once_with([1, 0, 1])

    @patch("py_i2c_register.register_segment.RegisterSegment.num_bytes_for_bits")
    def test_len_bytes(self, fn):
        self.reg.len_bytes()
        fn.assert_called_once_with(len(self.reg))

class TestRegisterAdd(unittest.TestCase):
    def test_perfect(self):
        reg = Register("NAME", 1, 2, "WRITEMODE", {})
        reg.add("SEG_NAME", 0, 2, [0] * 3)

        ret = reg.get("SEG_NAME")
        self.assertEqual(ret.name, "SEG_NAME")
        self.assertEqual(ret.lsb_i, 0)
        self.assertEqual(ret.msb_i, 2)
        self.assertEqual(ret.bits, [0] * 3)

class TestRegisterRead(unittest.TestCase):
    def test_perfect(self):
        i2c = MagicMock()
        i2c.readBytes = MagicMock(return_value=[213, 170])

        reg = Register("NAME", 1, 2, Register.READ, {})
        reg.add("SEG_NAME", 0, 2, [0] * 3)

        reg.read(i2c)

        self.assertEqual(reg.get("SEG_NAME").bits, [1, 0, 1])

    def test_not_configured_to_read(self):
        i2c = MagicMock()

        reg = Register("NAME", 1, 2, Register.WRITE, {})
        reg.add("SEG_NAME", 0, 2, [0] * 3)

        with self.assertRaises(AttributeError):
            reg.read(i2c)

    def test_not_enough_bytes_read(self):
        i2c = MagicMock()
        i2c.readBytes = MagicMock(return_value=[32])

        reg = Register("NAME", 1, 2, Register.READ, {})
        reg.add("SEG_NAME", 9, 11, [0] * 3)

        with self.assertRaises(KeyError):
            reg.read(i2c)

    def test_i2c_read_fail(self):
        i2c = MagicMock()
        i2c.readBytes = MagicMock(side_effect=Exception("Exception"))

        reg = Register("NAME", 1, 2, Register.READ, {})
        reg.add("SEG_NAME", 0, 2, [0] * 3)

        with self.assertRaises(SystemError):
            reg.read(i2c)

class TestRegisterWrite(unittest.TestCase):
    def setUp(self):
        self.reg = Register("NAME", 1, 2, Register.WRITE, {})
        self.reg.add("SEG_NAME", 0, 2, [0] * 3)

        self.i2c = MagicMock()
        self.i2c.writeBytes = MagicMock(return_value=None)

    def test_perfect(self):
        self.reg.get("SEG_NAME").bits = [0, 1, 1]

        self.reg.write(self.i2c)
        self.i2c.writeBytes.assert_called_once_with(1, 2, [6])

    def test_not_setup_to_write(self):
        self.reg.op_mode = Register.READ

        with self.assertRaises(AttributeError):
            self.reg.write(self.i2c)

    def test_non_cont_seg_bits(self):
        self.reg.add("BAD_SEG", 9, 11, [0] * 3)

        with self.assertRaises(SyntaxError):
            self.reg.write(self.i2c)

    def test_multiple_segments_managing_same_bit(self):
        self.reg.add("BAD_SEG", 2, 5, [0] * 4)

        with self.assertRaises(KeyError):
            self.reg.write(self.i2c)

    def test_multiple_segments_managing_same_bit_more_than_one_bit(self):
        self.reg.add("BAD_SEG1", 2, 5, [0] * 4)
        self.reg.add("BAD_SEG2", 5, 7, [0] * 3)

        with self.assertRaises(KeyError):
            self.reg.write(self.i2c)

    def test_i2c_write_fail(self):
        self.i2c.writeBytes.return_value = 1

        with self.assertRaises(SystemError):
            self.reg.write(self.i2c)

class TestRegisterGenericMethods(unittest.TestCase):
    def test_str(self):
        reg = Register("NAME", 1, 2, "OP_MODE", {})
        reg.add("SEG_NAME", 0, 2, [0] * 3)

        self.assertEqual(str(reg), "Register<name=NAME, address=2, op_mode=OP_MODE, segments={\n    SEG_NAME=RegisterSegment<name=SEG_NAME, lsb_i=0, msb_i=2, bits=[0, 0, 0]>\n}>")

    def test_len(self):
        reg = Register("NAME", 1, 2, "OP_MODE", {})
        reg.add("SEG1", 0, 2, [0] * 3)
        reg.add("SEG2", 3, 5, [0] * 3)

        self.assertEqual(len(reg), 6)
