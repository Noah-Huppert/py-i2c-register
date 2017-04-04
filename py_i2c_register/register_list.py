from py_i2c_register.register import Register
from py_i2c_register.register_segment import RegisterSegment

class RegisterList():
    """A wrapper class around multiple Registers
    Fields:
        - dev_addr(int): I2C address of device which registers are on
        - i2c(I2C Object): I2C Object used to read and write registers, see docs/i2c-object.md for details
        - registers(map<str, Register>): Map of Registers, Keys are Register names and values are the Registers themselves
    """

    """Creates a new RegisterList instance
    Args: Same as fields
    """
    def __init__(self, dev_addr, i2c, registers):
        self.dev_addr = dev_addr
        self.i2c = i2c
        self.registers = registers

    """Converts a RegisterSegment bit array into an integer
    Args:
        - reg_name(str): Name of Register which houses Segment
        - seg_name(str): Name of Segment in Register
        - read_first(bool): If True the register will be read first
        
    Returns:
        - int: Integer value of Segment in Register
        
    Raises:
        - KeyError: If Register or Segment name provided does not exist
    """
    def to_int(self, reg_name, seg_name, read_first=False):
        # Convert value and return
        return self.get(reg_name, read_first=read_first).get(seg_name).bytes_to_int()

    """Converts a RegisterSegment bit array into an integer using two's compliment
    Args:
        - reg_name(str): Name of Register which houses Segment
        - seg_name(str): Name of Segment in Register
        - read_first(bool): If True the register will be read first
        
    Returns:
        - int: Integer value of Segment in Register
        
    Raises:
        - KeyError: If Register or Segment name provided does not exist
    """
    def to_twos_comp_int(self, reg_name, seg_name, read_first=False):
        return self.get(reg_name, read_first=read_first).get(seg_name).bytes_to_twos_comp_int()

    """Sets bits of RegisterSegment
    Args:
        - reg_name(str): Name of Register which segment is in
        - seg_name(str): Name of Segment to set bits for
        - bits(int[]): Bits to set
        - write_after(bool): If True will write register after bits are set
        - write_fn: Function used to write if not None
        
    Raises:
        - KeyError: If Register or Segment with provided name does not exist
        - IndexError: If bits array is not length set by Segment lsb_i and msb_i
        - ValueError: If bits array contains element with values other than 0 or 1
    """
    def set_bits(self, reg_name, seg_name, bits, write_after=False, write_fn=None):
        self.get(reg_name).get(seg_name).set_bits(bits)

        if write_fn is None:
            write_fn = self.write

        if write_after:
            write_fn(reg_name)

    """Sets bits of RegisterSegment from integer value
    Args:
        - reg_name: Same as Register.set_bits
        - seg_name: Same as Register.set_bits
        - val(int): Integer value to set
        - write_after: Same as Register.set_bits
        - write_fn: Function used to write if not None
        
    Raises: 
        - KeyError: Same as Register.set_bits
        - ValueError: If value provided can not be represented in Segment size
    """
    def set_bits_from_int(self, reg_name, seg_name, val, write_after=False, write_fn=None):
        seg = self.get(reg_name).get(seg_name)
        bits = RegisterSegment.to_bits(val, len(seg))

        self.set_bits(reg_name, seg_name, bits, write_after=write_after, write_fn=write_fn)

    """Add Register to register list
    Args: Same arguments as Register.__init__
    Returns:
        - Register: Recently added register, for chaining
      
    Raises:
        - KeyError: If register with name already exists
    """
    def add(self, name, address, op_mode, segments):
        if name in self.registers:
            raise KeyError("RegisterSegment with name already exists: name: {}".format(name))

        self.registers[name] = Register(name, self.dev_addr, address, op_mode, segments)
        return self.registers[name]

    """Get register with name
    Args:
      - name(str): Register name
      - read_first(bool): If True will read the Register with provided name first
      
    Returns:
      - Register: Register with specified name
      
    Raises:
      - KeyError: If register with name does not exist
    """
    def get(self, name, read_first=False):
        if name not in self.registers:
            raise KeyError("Register with name \"{}\" not found".format(name))

        # Read first if asked
        if read_first:
            self.read(name)

        return self.registers[name]

    """Read register
    Args:
      - name(str): Name of register to read
      
    Returns:
      - Register: Register that was read, with updated values
      
    Raises:
      - KeyError: If register with provided name does not exist
      - AttributeError: If register is not set up to read
    """
    def read(self, name):
        return self.get(name).read(self.i2c)

    """Write register
    Args:
      - name(str): Name of register to write
      
    Returns:
      - Register: Register that was written, for chaining
      
    Raises:
      - KeyError: If register with provided name does not exist
      - AttributeError: If register is not set up to write
    """
    def write(self, name):
        return self.get(name).write(self.i2c)

    """String representation of RegisterList
    Returns:
        - str: String representation of RegisterList
    """
    def __str__(self):
        out = "RegisterList<device_address={}, registers={{\n".format(self.dev_addr)

        for k in self.registers:
            v = self.registers[k]
            # Indent output from Register.str
            v = str(v)
            v = v.split("\n")

            newV = ""
            for i in range(0, len(v)):
                # Don't indent first line
                if i != 0:
                    newV += "    "

                newV += v[i]

                # No newline on last line
                if i != len(v) - 1:
                    newV += "\n"

            out += "    {}={}\n".format(k, newV)

        out += "}>"
        return out
