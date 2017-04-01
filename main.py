import re, math, time

from flask import Flask, jsonify
from OmegaExpansion import onionI2C

class RegisterSegment():
    """Class which holds information about section of register
    Fields:
      - name(str): Name of segment
      - lsb_i(int): Index of LSB
      - msb_i(int): Index of MSB
      - bits(int[]): List of bits, each element of list is either 0 or 1
    """

    """Converts a given number to a bit array
    Args:
        - number(int): Number to convert, must be in range [0, 2^size]
        - size(int): Number of bits used to represent number
    
    Return:
        - int[]: Array of integers representing number
      
    Raises:
        - ValueError: If number can not be represented by number of bits specified in size
    """
    @staticmethod
    def to_bits(number, size):
        if number < 0 or number > math.pow(2, size):
            raise ValueError(
                "Number provided must be in range: [0, {}], was: {}".format(int(math.pow(2, size)), number))

        bits = []
        for bit in format(number, "0{}b".format(size)):
            bits.append(int(bit))

        return bits

    """Converts an array of bits into an integer
    Args:
        - bits(int[]): Array of bits to convert into an integer
        
    Returns:
        - int: Bits in integer form
    """
    @staticmethod
    def to_int(bits):
        out = 0
        for bit in bits:
            out = (out << 1) | bit

        return out

    @staticmethod
    def to_two_comp_int(bits):
        bits_str = ""

        for b in bits:
            bits_str += str(b)

        size = len(bits)
        v = int(bits_str, 2)

        if (v & (1 << (size - 1))) != 0:
            v = v - (1 << size)

        return v



    """Calculate the minimum number of bytes needed to store a given number of bits
    Divides by 8 and rounds up
    """
    @staticmethod
    def num_bytes_for_bits(bits):
        return int(math.ceil(float(bits) / 8.0))

    """Converts an array of bits into a padded bytes array
    This just splits the bits array into groups of 8. It then fills any space at the end with 0s. The pairs of 8 bits are 
    then converted into integers.
    
    Args:
        - bits(int[]): Bits to convert into padded byte array
    
    Returns:
        - int[]: Byte array representation of self.bits
    """
    @staticmethod
    def to_padded_byte_arr(bits):
        bytes = []
        byte_slice_lower = 0  # Increases by 8 for each byte
        for byte_i in range(RegisterSegment.num_bytes_for_bits(len(bits))):
            # Check that upper limit isn't too big
            byte_slice_upper = byte_i * 8
            to_pad = 0  # Used to keep track of how many 0s we need to pad the end of this byte with
            if byte_slice_upper > len(bits) - 1:
                # Resize if it is
                byte_slice_upper = len(bits) - 1

                # Also keep track of the fact that we need to pad the end of this byte with some 0s
                to_pad = byte_slice_upper - len(bits)

            # Convert
            byte_slice = bits[byte_slice_lower:byte_slice_upper]
            byte = RegisterSegment.to_int(byte_slice)
            bytes.append(byte)

            # Append padding
            if to_pad > 0:
                bytes.append([0] * to_pad)

            # Add 8 to lower slice bound for next byte
            byte_slice_lower += 8

        return bytes

    """Creates a Register Segment instance
    Raises:
        - IndexError: If length of bits array is less than that defined by lsb_i and msb_i
        - ValueError: If lsb_i or msb_i is not in the range [0, 7] or lsb_i and msb_i are greater or less than each other 
                      in wrong way
    """
    def __init__(self, name, lsb_i, msb_i, bits):
        self.name = name

        # LSB and MSB indexes
        """
        if lsb_i < 0 or lsb_i > 7:
            raise ValueError("LSB index can not be less than 0 or greater than 6, was: {}".format(lsb_i))

        if msb_i < 0 or msb_i > 7:
            raise ValueError("MSB index can not be less than 1 or greater than 7, was: {}".format(msb_i))
        """

        if lsb_i > msb_i:
            raise ValueError("LSB index can not be greater than MSB index, lsb_i: {}, msb_i: {}".format(lsb_i, msb_i))

        if msb_i < lsb_i:
            raise ValueError("MSB index can not be less thans LSB index, lsb_i: {}, msb_i: {}".format(lsb_i, msb_i))

        self.lsb_i = lsb_i
        self.msb_i = msb_i

        # Bit array
        self.set_bits(bits)

    """Calls RegisterSegment.to_int on self.bits
    Returns:
        - int: Bits in integer form
    """
    def bytes_to_int(self):
        return RegisterSegment.to_int(self.bits)

    def bytes_to_twos_comp_int(self):
        return RegisterSegment.to_two_comp_int(self.bits)

    """Update RegisterSegment bits from given bytes array
    Args:
        - bytes(int[]): Bytes array to update bits values from
        
    Raises:
        - KeyError: If provided bytes array does not contain enough bytes to fill RegisterSegment values
    """
    def update_bits(self, bytes):
        # Check that bytes array contains values inside lsb_i and msb_i range
        min_bytes = RegisterSegment.num_bytes_for_bits(self.msb_i + 1)
        if len(bytes) < min_bytes:
            raise KeyError("Provided bytes array does not contain enough bytes to fill MSB, bytes: {}, MSB index: {}, required bytes length: {}".format(bytes, self.msb_i, min_bytes))

        # Determine start and end byte by dividing lsb_i by 8 and rounding down
        start_byte = int(math.floor(float(self.lsb_i) / 8.0))
        end_byte = int(math.floor(float(self.msb_i) / 8.0))

        # Convert needed bytes into bits
        # Keys will be offset by start_byte
        needed_bytes_as_bits = []

        for byte_i in range(start_byte, end_byte + 1):
            byte = bytes[byte_i]
            converted_bits = RegisterSegment.to_bits(byte, 8)

            # Convert bits and check bits are all 0 or 1
            for i in range(len(converted_bits)):
                bit = converted_bits[i]
                bit = int(bit)

                if bit != 0 and bit != 1:
                    raise ValueError("Bits can only have the value 0 or 1, was: {}, bit_i: {}, byte_i: {}".format(bit, i, byte_i))

                converted_bits[i] = bit

            needed_bytes_as_bits.append(converted_bits)

        # Loop through bits
        #print("lsb_i={}, msb_i={}, self.bits={}, needed_bytes_as_bits={}".format(self.lsb_i, self.msb_i, self.bits, needed_bytes_as_bits))
        for bit_i in range(self.lsb_i, self.msb_i + 1):
            in_byte_i = int(math.floor(float(bit_i) / 8.0))
            bit_offset = (in_byte_i * 8)  # Used to figure out which bit in the byte we are in

            #print("bit_i={}, in_byte_i={}, bit_offset={}".format(bit_i, in_byte_i, bit_offset))

            self.bits[bit_i - self.lsb_i] = needed_bytes_as_bits[in_byte_i - start_byte][bit_i - bit_offset]

    """Set Segment bits
    Args:
        - bits(int[]): Array of bits to set
    
    Raises:
        - IndexError: If length of bits array is less than that defined by lsb_i and msb_i
        - ValueError: If an element of the provided bits array is not equal to 0 or 1
    """
    def set_bits(self, bits):
        if len(bits) != len(self):
            raise IndexError(
                "Default list must be size that specified by lsb_i and msb_i, was: {}, should be: {}".format(len(bits),
                                                                                                             len(self)))

        i = 0
        for bit in bits:
            if bit != 0 and bit != 1:
                raise ValueError("Bits can only have the integer values 0 or 1, was: {}, bit_i: {}".format(bit, i))

            i += 1

        self.bits = bits

    def __str__(self):
        return "RegisterSegment<name={}, lsb_i={}, msb_i={}, bits={}>".format(self.name, self.lsb_i, self.msb_i,
                                                                              self.bits)

    """Get length of register segment
    Uses lsb_i and msb_i to calculate
    """
    def __len__(self):
        return self.msb_i - self.lsb_i + 1


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
    """
    def set_bits(self, name, bits):
        self.get(name).set_bits(bits)

    """Add Register segment
    Args: Same as RegisterSegment.__init__
    Returns:
      - Register: Self, for chaining
    """
    def add(self, name, lsb_i, msb_i, bits):
        self.segments[name] = RegisterSegment(name, lsb_i, msb_i, bits)
        return self

    """Reads register
    Args:
      - reg_list(RegisterList): Register list register belongs to
    
    Returns:
      - Register: Self with updated values, for chaining
      
    Raises:
      - AttributeError: If register is not configured to read
      - KeyError: If a register segment requests a bit that was not read
    """
    def read(self, i2c):
        if Register._read_pattern.match(self.op_mode) is not None:
            # Get number of bytes to read, will raise AssertionError if segments do not create round number of bytes
            bytes_count = self.len_bytes()
            read_bytes = i2c.readBytes(self.dev_addr, self.reg_addr, bytes_count)

            # Loop through each byte read and map to elements in RegisterSegment bit arrays
            for k, segment in self.segments.iteritems():
                segment.update_bits(read_bytes)  # Raises KeyError if we didn't read enough bytes

        else:
            raise AttributeError("Register {} is not set up to allow read operations, op_mode: \"{}\"".format(self.name, self.op_mode))

    """Writes register
    Args:
      - reg_list(RegisterList): Register list register belongs to
      
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

            for k, segment in self.segments.iteritems():
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
            for k, v in bits.iteritems():
                bits_arr.append(v)

            # Create bytes array
            bytes_arr = RegisterSegment.to_padded_byte_arr(bits_arr)

            # Write to i2c
            write_status = i2c.writeBytes(self.dev_addr, self.reg_addr, bits_arr)

            if write_status == 1:
                raise SystemError("Failed to write to i2c")
        else:
            raise AttributeError("Register {} is not set up to allow write operations, op_mode: \"{}\"".format(self.name, self.op_mode))

    def __str__(self):
        out = "Register<name={}, address={}, op_mode={}, segments={{\n".format(self.name, self.reg_addr, self.op_mode)

        for k, v in self.segments.iteritems():
            out += "    {}={}\n".format(k, str(v))

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
        for k, segment in self.segments.iteritems():
            l += len(segment)

        return l

class RegisterList():
    def __init__(self, dev_addr, registers):
        self.dev_addr = dev_addr
        self.i2c = onionI2C.OnionI2C()
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

    def to_twos_comp_int(self, reg_name, seg_name, read_first=False):
        return self.get(reg_name, read_first=read_first).get(seg_name).bytes_to_twos_comp_int()

    """Sets bits of RegisterSegment
    Args:
        - reg_name(str): Name of Register which segment is in
        - seg_name(str): Name of Segment to set bits for
        - bits(int[]): Bits to set
        - write_after(bool): If True will write register after bits are set
        - write_fn: Function used to write
        
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
        - write_fn: Function used to write
        
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
        if name in segments:
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

    def __str__(self):
        out = "RegisterList<device_address={}, registers={{\n".format(self.device_address)

        for k, v in self.registers.iteritems():
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

class LidarLight():
    # Register and Segment name constants
    REG_ACQ_COMMAND = "ACQ_COMMAND"
    SEG_ACQ_COMMAND = REG_ACQ_COMMAND

    REG_STATUS = "STATUS"
    SEG_PROC_ERROR_FLAG = "PROC_ERROR_FLAG"
    SEG_HEALTH_FLAG = "HEALTH_FLAG"
    SEG_SECONDARY_RET_FLAG = "SECONDARY_RET_FLAG"
    SEG_INVALID_SIGNAL_FLAG = "INVALID_SIGNAL_FLAG"
    SEG_SIGNAL_OVERFLOW_FLAG = "SIGNAL_OVERFLOW_FLAG"
    SEG_REFERENCE_OVERFLOW_FLAG = "REFERENCE_OVERFLOW_FLAG"
    SEG_BUSY_FLAG = "BUSY_FLAG"

    REG_PEAK_CORR = "PEAK_CORR"
    SEG_PEAK_CORR = REG_PEAK_CORR

    REG_VELOCITY = "VELOCITY"
    SEG_VELOCITY= REG_VELOCITY

    REG_OUTER_LOOP_COUNT = "OUTER_LOOP_COUNT"
    SEG_OUTER_LOOP_COUNT = REG_OUTER_LOOP_COUNT

    REG_DISTANCE = "DISTANCE"
    SEG_DISTANCE = "DISTANCE"

    def __init__(self):
        # Configure control registers
        self.controls = RegisterList(0x62, {})
        self.controls.add(LidarLight.REG_ACQ_COMMAND, 0x00, Register.WRITE, {}) \
            .add(LidarLight.SEG_ACQ_COMMAND, 0, 7, [0] * 8)

        self.controls.add(LidarLight.REG_STATUS, 0x01, Register.READ, {}) \
            .add(LidarLight.SEG_PROC_ERROR_FLAG, 6, 6, [0]) \
            .add(LidarLight.SEG_HEALTH_FLAG, 5, 5, [0]) \
            .add(LidarLight.SEG_SECONDARY_RET_FLAG, 4, 4, [0]) \
            .add(LidarLight.SEG_INVALID_SIGNAL_FLAG, 3, 3, [0]) \
            .add(LidarLight.SEG_SIGNAL_OVERFLOW_FLAG, 2, 2, [0]) \
            .add(LidarLight.SEG_REFERENCE_OVERFLOW_FLAG, 1, 1, [0]) \
            .add(LidarLight.SEG_BUSY_FLAG, 0, 0, [0])

        self.controls.add(LidarLight.REG_PEAK_CORR, 0x0c, Register.READ, {})\
            .add(LidarLight.SEG_PEAK_CORR, 0, 7, [0] * 8)

        self.controls.add(LidarLight.REG_VELOCITY, 0x09, Register.READ, {})\
            .add(LidarLight.SEG_VELOCITY, 0, 7, [0] * 8)

        self.controls.add(LidarLight.REG_OUTER_LOOP_COUNT, 0x11, Register.READ + Register.WRITE, {})\
            .add(LidarLight.SEG_OUTER_LOOP_COUNT, 0, 7, [0] * 8)

        self.controls.add(LidarLight.REG_DISTANCE, 0x8f, Register.READ, {})\
            .add(LidarLight.SEG_DISTANCE, 0, 15, [0] * 16)

    """Writes Register with given name when device is ready
    Determines when device is ready by polling  STATUS.BUSY_FLAG until 0
    
    Args:
        - name(str): Name of register to write
        - max_count(int): Maximum number of times program will loop while waiting for STATUS.BUSY_FLAG to become 0
        - count_delay(float): Delay between each loop while waiting for STATUS.BUSY_FLAG to become 0
    
    Raises:
        - SystemError: If max_count is reached and STATUS.BUSY_FLAG is not 0
        - KeyError: If Register with name is not found
        - ValueError: If max_count is less than 1
    """
    def write_when_ready(self, name, max_count=999, count_delay=0.01):
        # Check max_count is at least 1 so loop below runs
        if max_count < 1:
            raise ValueError("max_count must be >= 1")

        # Check STATUS.BUSY_FLAG
        count = 0
        while count < max_count:
            # Read register
            self.controls.read(LidarLight.REG_STATUS)

            # Check BUSY_FLAG
            busy_flag = self.controls.to_int(LidarLight.REG_STATUS, LidarLight.SEG_BUSY_FLAG)

            if busy_flag == 0:
                # If not busy, write
                return self.controls.write(name)
            else:
                # Otherwise sleep
                time.sleep(count_delay)

            count += 1

        # Raise error if loop exited
        raise SystemError("max_count reached while waiting for STATUS.BUSY_FLAG to become 0, max_count: {}, count_delay: [}".format(max_count, count_delay))

    """Sets bits of RegisterSegment and then writes when the device is ready
    Args:
        - reg_name(str): Name of register to write
        - seg_name(str): Name of segment to write
        - bits(int[]): Bits to write
    """
    def set_bit_when_ready(self, reg_name, seg_name, bits):
        self.controls.set_bits(reg_name, seg_name, bits, write_after=True, write_fn=self.write_when_ready)

    """Sets bits of RegisterSegment and then writes when the device is ready
    Args:
        - reg_name(str): Name of register to write
        - seg_name(str): Name of segment to write
        - val(int): Integer to write
    """
    def set_bit_when_ready_from_int(self, reg_name, seg_name, val):
        self.controls.set_bits_from_int(reg_name, seg_name, val, write_after=True, write_fn=self.write_when_ready)

    """Resets device
    """
    def reset(self):
        self.set_bit_when_ready_from_int(LidarLight.REG_ACQ_COMMAND, LidarLight.SEG_ACQ_COMMAND, 0x00)

    """Sets up Lidar Light device
    """
    def setup(self):
        self.set_bit_when_ready_from_int(LidarLight.REG_ACQ_COMMAND, LidarLight.SEG_ACQ_COMMAND, 0x04)

    def setup_indefinite_measurements(self):
        self.set_bit_when_ready_from_int(LidarLight.REG_ACQ_COMMAND, LidarLight.SEG_ACQ_COMMAND, 0x04)
        self.set_bit_when_ready_from_int(LidarLight.REG_OUTER_LOOP_COUNT, LidarLight.SEG_OUTER_LOOP_COUNT, 0xff)

lidar = LidarLight()
lidar.reset()
lidar.setup_indefinite_measurements()

app = Flask(__name__)

@app.route("/")
def route_home():
    return app.send_static_file("index.html")

@app.route("/distance")
def route_distance():
    # Trigger read
    lidar.set_bit_when_ready_from_int(LidarLight.REG_ACQ_COMMAND, LidarLight.SEG_ACQ_COMMAND, 0x04)

    # Get distance
    distance = lidar.controls.to_int(LidarLight.REG_DISTANCE, LidarLight.SEG_DISTANCE, read_first=True)

    return jsonify(distance)

@app.route("/velocity")
def route_velocity():
    velocity = lidar.controls.to_twos_comp_int(LidarLight.REG_VELOCITY, LidarLight.SEG_VELOCITY, read_first=True)

    return jsonify(velocity)

if __name__== '__main__':
    app.run(host="0.0.0.0")
