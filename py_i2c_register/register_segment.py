import math

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
            bits.insert(0, int(bit))

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
        l = len(bits)
        for bit in reversed(bits):
            out = (out << 1) | bit

        return out

    """Converts an array of bits arranged in two's compliment form into an integer
    Args:
        - bits(int[]): Array of bits to convert into an integer
        
    Returns:
        - int: Bits in integer form
    """
    @staticmethod
    def to_twos_comp_int(bits):
        bits_str = ""

        for b in reversed(bits):
            bits_str += str(b)

        size = len(bits)
        v = int(bits_str, 2)

        if (v & (1 << (size - 1))) != 0:
            v = v - (1 << size)

        return v

    """Calculate the minimum number of bytes needed to store a given number of bits
    Divides by 8 and rounds up.
    
    Args:
        - bits(int): The number of bits
    
    Returns:
        - int: The minimum number of bytes required to store number of bits
    """
    @staticmethod
    def num_bytes_for_bits(bits):
        return int(math.ceil(float(bits) / 8.0))

    """Converts an array of bits into a padded bytes array
    This just splits the bits array into groups of 8. It then fills any space at the end of the last pair with 0s. 
    The pairs of 8 bits are then converted into integers, and returned as a byte array.
    
    Args:
        - bits(int[]): Bits to convert into padded byte array
    
    Returns:
        - int[]: Byte array representation of bits
    """
    @staticmethod
    def to_padded_byte_arr(bits):
        bytes = []
        byte_slice_lower = 0  # Increases by 8 for each byte

        # Determine how many bytes the provided bits are and loop that many times
        # Each loop "synthesizes" a new byte from the bits array
        for byte_i in range(RegisterSegment.num_bytes_for_bits(len(bits))):
            # Check that upper limit isn't too big
            byte_slice_upper = ((byte_i + 1) * 8) - 1  # The index we *want* to slice to
            to_pad = 0  # Used to keep track of how many 0s we need to pad the end of this byte
            if byte_slice_upper > len(bits) - 1:
                # Keep track of the fact that we need to pad the end of this byte with some 0s
                to_pad = byte_slice_upper - (len(bits) - 1)

                # Resize if index we wanted to slice to is too big
                byte_slice_upper = len(bits) - 1


            # Convert
            # Add 1 to byte_slice_upper because upper range of slice is not inclusive
            byte_slice = bits[byte_slice_lower:byte_slice_upper + 1]

            # Append padding
            if to_pad > 0:
                byte_slice.extend([0] * to_pad)

            byte = RegisterSegment.to_int(byte_slice)
            bytes.append(byte)

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

        # Sanity check LSB and MSB indexes
        if lsb_i > msb_i:
            raise ValueError("LSB index can not be greater than MSB index, lsb_i: {}, msb_i: {}".format(lsb_i, msb_i))

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

    """Calls RegisterSegment.to_twos_comp_into on self.bits
    Returns:
        - int: Bits converted to integer form by reversing two's compliment
    """
    def bytes_to_twos_comp_int(self):
        return RegisterSegment.to_twos_comp_int(self.bits)

    """Update RegisterSegment bits from given bytes array
    The bytes array is assumed to be the complete data read off of a register. Thus the first byte's LSB will be 
    treated as index 0 when dealing with the lsb_i and msb_i of the RegisterSegment.
    
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
                converted_bits[i] = int(converted_bits[i])

            needed_bytes_as_bits.append(converted_bits)

        # Loop through bits
        for bit_i in range(self.lsb_i, self.msb_i + 1):
            in_byte_i = int(math.floor(float(bit_i) / 8.0))
            bit_offset = (in_byte_i * 8)  # Used to figure out which bit in the byte we are in

            self.bits[bit_i - self.lsb_i] = needed_bytes_as_bits[in_byte_i - start_byte][bit_i - bit_offset]

    """Set Segment bits
    Runs some sanity checks on the new bits before setting them.
    
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
    Uses lsb_i and msb_i to calculate.
    
    Returns:
        - int: Number of bits represented by RegisterSegment.
    """
    def __len__(self):
        return self.msb_i - self.lsb_i + 1

