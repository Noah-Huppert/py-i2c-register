# I2C Object
The I2C Register library assumes a theoretical "I2C Object" is passed to any read or write related functions. This 
allows the library to stay platform agnostic with minimal effort. 

This I2C Object should have the following functions:
## readBytes(device_addr, reg_addr, num_bytes)
This function will read a specific number of bytes from a register on a device.

### Args
- device_addr(int): The I2C address of the device to read from.
- reg_addr(int): The I2C address of the register on the device to read from.
- num_bytes(int): The number of bytes to read from the register on the device.

### Returns
Nothing.

### Raises
Any error that subclasses `Exception` if the I2C read fails.

## writeBytes(device_addr, reg_addr, bytes_arr)
This function will write the contents of a byte array to a register on a device.

### Args
- device_addr(int): The I2C address of the device to write to.
- reg_addr(int): The I2C address of the register to write to.
- bytes_arr(int[]): Array of bytes to write to the register on the device.

### Returns
The integer `1` if the write fails, any other return value is treated as a success.

### Raises
Nothing

# I2C Object uses
The I2C Object is used in 3 places in the I2C Register library. 

The `Register.read` and `Register.write` methods take an I2C Object as their only argument. They use it to communicate 
with registers over I2C. The `RegisterList` constructor also takes an I2C Object as an parameter. The `RegisterList` uses 
this I2C Object to call `Register.read` and `Register.write` in some helper methods of its own. 
