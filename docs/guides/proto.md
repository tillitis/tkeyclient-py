# Working with the TKey protocol

This package includes a [`tkeyclient.proto`](../reference/tkeyclient/proto.md) module which has helper functions
that is used to work with the TKey protocol, in order to communicate with the
underlying serial device.

## The protocol

You can find the official developer documentation for the TKey protocol [here](https://dev.tillitis.se/protocol/).

## Serial communication

This package depends on [pySerial](https://pyserial.readthedocs.io/) for all interaction with serial devices, which is what the TKey register as when connected to your system.

To use a serial device in Python, create an instance of `serial.Serial`:

```python
import serial
conn = serial.Serial('/dev/ttyACM0')
conn.write('testing') # Write to the serial device
conn.read(1024)       # Read 1024 bytes from the serial device
```

## Using the protocol helpers

Here are some examples on how to use the protocol helper functions that the
[`tkeyclient.proto`](../reference/tkeyclient/proto.md) module provides.

### Send a command to the TKey

To send a command and get the response, you can do like this:

```python
import serial
import tkeyclient.proto as proto

# Open connection to serial device (with required parameters for a TKey)
conn = serial.Serial('/dev/ttyACM0', baudrate=62500, timeout=1)

# Create valid protocol frame for sending FW_CMD_NAME_VERSION (0x01)
data = proto.create_frame(proto.cmdNameVersion, 1, 2)

# Write data to device and read the response
bytes_written = proto.write_frame(conn, data)
response = proto.read_frame(conn)

# Parse the response header (first byte)
frame_id, endpoint, status, length = proto.parse_header(response[0])

# Show response status and length
print(status, length)

# Show the entire response (in hex and binary)
proto.debug_frame(response)
```
