import unittest

from mock import MagicMock

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

