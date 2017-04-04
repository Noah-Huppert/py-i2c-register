import re
from py_i2c_register.register_segment import RegisterSegment

class Register():
    """Wrapper class around a register on an i2c accessible device
    Fields:
      - name(str): Name of register, key used to access it
      - reg_addr(int): Address of register
      - dev_addr(int): Address of i2c device
      - op_mode(int): Flags which specify which kind of data operations can take place on register
      - bits(int or Bit[]): Number of Register Bit objects or array of Register Bit objects
    """
    READ = "READ"
    _read_pattern = re.compile(".*{}.*".format(READ))
    WRITE = "WRITE"
    _write_pattern = re.compile(".*{}.*".format(WRITE))

    """Creates a Register instance
    Args: Same as Fields
    """
    def __init__(self, name, dev_addr, reg_addr, op_mode, segments={}):
        self.name = name
        self.dev_addr = dev_addr
        self.reg_addr = reg_addr
        self.op_mode = op_mode
        self.segments = segments

    """Get RegisterSegment by name
    Returns:
        - RegisterSegment: RegisterSegment with name provided
    
    Raises:
        - KeyError: If no RegisterSegment with name provided exists
    """
    def get(self, name):
        if name not in self.segments:
            raise KeyError("No segment found with name: \"{}\"".format(name))

        return self.segments[name]

    """Set bits of Segment with name provided
    Args:
        - name(str): Name of Segment to set bits of
        - bits(int[]): Bits to set
    
    Raises:
        - KeyError: If Segment with name provided does not exist
        - IndexError: If length of bits array is less than that defined by lsb_i and msb_i
        - ValueError: If an element of the provided bits array is not equal to 0 or 1
    """
    def set_bits(self, name, bits):
        self.get(name).set_bits(bits)

    """Add Register segment
    Args: Same as RegisterSegment.__init__
    Returns:
      - Register: The current Register, for chain adding of RegisterSegments to same Register
    """
    def add(self, name, lsb_i, msb_i, bits):
        self.segments[name] = RegisterSegment(name, lsb_i, msb_i, bits)
        return self

    """Reads register
    Args:
      - i2c(I2C Object): I2C object used to communicate with i2c system, see docs/i2c-object.md for more information
    
    Raises:
      - AttributeError: If register is not configured to read
      - KeyError: If a register segment requests a bit that was not read
      - SystemError: If the I2C Object fails to read
    """
    def read(self, i2c):
        if Register._read_pattern.match(self.op_mode) is not None:
            # Get number of bytes to read, will raise AssertionError if segments do not create round number of bytes
            bytes_count = self.len_bytes()
            read_bytes = []

            try:
                read_bytes = i2c.readBytes(self.dev_addr, self.reg_addr, bytes_count)
            except Exception as e:
                raise SystemError("Failed to read i2c: {}".format(e))

            # Loop through each byte read and map to elements in RegisterSegment bit arrays
            for segment in self.segments:
                self.segments[segment].update_bits(read_bytes)  # Raises KeyError if we didn't read enough bytes

        else:
            raise AttributeError("Register {} is not set up to allow read operations, op_mode: \"{}\"".format(self.name, self.op_mode))

    """Writes register
    Args:
      - i2c(I2C Object): I2C object used to communicate with i2c system, see docs/i2c-object.md for more information
      
    Returns:
      - Register: Self for chaining
      
    Raises:
      - AttributeError: If register is not set up to write
      - SyntaxError: If RegisterSegments are not configured to make a continuous series of bits
      - KeyError: If two RegisterSegments are configured to manage the same bit
      - SystemError: Failed to write i2c
    """
    def write(self, i2c):
        if Register._write_pattern.match(self.op_mode) is not None:
            bits = {}
            managing_segment = {}
            max_bit_i = 0

            for segment in self.segments:
                segment = self.segments[segment]

                for bit_i in range(len(segment.bits)):
                    actual_bit_i = bit_i + segment.lsb_i
                    # Record maximum bit index for continuous test later
                    if actual_bit_i > max_bit_i:
                        max_bit_i = actual_bit_i

                    # Mark which segment manages bit in case of configuration error
                    if actual_bit_i not in managing_segment:
                        managing_segment[actual_bit_i] = []
                    managing_segment[actual_bit_i].append(segment.name)

                    bits[bit_i + segment.lsb_i] = segment.bits[bit_i]

            # Check bits are continuous and only 1 segment controls each bit
            cont_check_err_is = []  # Indexes where bit array is not continuous
            managing_segment_check_err_is = []  # Indexes where more than 1 RegisterSegment is controlling a bit
            for bit_i in range(max_bit_i + 1):
                # Continuous check
                if bit_i not in bits:
                    cont_check_err_is.append(bit_i)

                # Managing segment check
                if (bit_i in managing_segment) and (len(managing_segment[bit_i]) > 1):
                    managing_segment_check_err_is.append(bit_i)

            # Raise errors if there where any
            if len(cont_check_err_is) > 0:
                raise SyntaxError("RegisterSegments are not configured to make a continuous series of bits, no values at indexes: {}".format(cont_check_err_is))

            if len(managing_segment_check_err_is) > 0:
                indexes_msg = ""

                for i in range(len(managing_segment_check_err_is)):
                    bit_i = managing_segment_check_err_is[i]
                    indexes_msg += "{} (competing segments: {})".format(bit_i, managing_segment[bit_i])

                    if i != len(managing_segment_check_err_is) - 1:
                        indexes_msg += ", "

                raise KeyError("More than one RegisterSegment is managing the following bit indexes: {}".format(indexes_msg))

            # Convert from bits map to bits array
            bits_arr = []
            for key in bits:
                bit = bits[key]
                bits_arr.append(bit)

            # Create bytes array
            bytes_arr = RegisterSegment.to_padded_byte_arr(bits_arr)

            # Write to i2c
            write_status = i2c.writeBytes(self.dev_addr, self.reg_addr, bytes_arr)

            if write_status == 1:
                raise SystemError("Failed to write to i2c")
        else:
            raise AttributeError("Register {} is not set up to allow write operations, op_mode: \"{}\"".format(self.name, self.op_mode))

    """String representation of Register
    Returns:
        - str: String representation of Register
    """
    def __str__(self):
        out = "Register<name={}, address={}, op_mode={}, segments={{\n".format(self.name, self.reg_addr, self.op_mode)

        for key in self.segments:
            segment = self.segments[key]
            out += "    {}={}\n".format(key, str(segment))

        out += "}>"
        return out

    """Length of register is bytes
    Returns:
        - int: The total number of bytes the register has, rounds up
    """
    def len_bytes(self):
        return RegisterSegment.num_bytes_for_bits(len(self))

    """Length of register in bits
    Returns:
        - int: The total number of bits the register has
    """
    def __len__(self):
        l = 0
        for segment in self.segments:
            l += len(self.segments[segment])

        return l
