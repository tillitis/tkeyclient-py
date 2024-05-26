import serial

from typing import Tuple
from collections import namedtuple

import tkeyclient.error as error


# ID values for firmware/application endpoints
ENDPOINT_FW = 2
ENDPOINT_APP = 3

# Named tuples for command and response frames
fwCommand = namedtuple('fwCommand', ['id', 'length'])

cmdNameVersion      = fwCommand(0x01, 0)
rspNameVersion      = fwCommand(0x02, 2)
cmdLoadApp          = fwCommand(0x03, 3)
rspLoadApp          = fwCommand(0x04, 1)
cmdLoadAppData      = fwCommand(0x05, 3)
rspLoadAppData      = fwCommand(0x06, 1)
rspLoadAppDataReady = fwCommand(0x07, 3)

# Data lengths for use with command/response frames
PROTO_DATA_LENGTH = [
    1,   # 0
    4,   # 1
    32,  # 2
    128  # 3
]


# TKey Framing protocol
# =====================================================================
#
# Bit     [7] (1 bit).  Reserved - possible protocol version.
# Bits [6..5] (2 bits). Frame ID tag:
#
# Note that the client application sets the frame ID tag. The ID tag in a
# given command must be preserved in the corresponding response to the
# command.
#
# Bits [4..3] (2 bits). Endpoint number:
#
# 0. HW in interface_fpga (unused)
# 1. HW in application_fpga (unused)
# 2. FW in application_fpga
# 3. SW (device application) in application_fpga
#
# Bit     [2] (1 bit).
#
# Unused for commands. MUST be zero.
# Responses: 0 = OK, 1 = Not OK (NOK)
#
# Bits [1..0] (2 bits). Command data length:
#
# 0. 1 byte
# 1. 4 bytes
# 2. 32 bytes
# 3. 128 bytes
#
# Note that the number of bytes indicated by the command data length field
# does not include the command header byte. This means that a complete
# command frame, with a header indicating a data length of 128 bytes, is
# 128+1 bytes in length.


def create_frame(cmd: fwCommand, frame_id: int, endpoint: int) -> bytearray:
    """
    Create protocol frame

    """
    if cmd.id > 255:
        raise error.TKeyProtocolError('Command ID must not exceed one byte [0..255]')
    if frame_id > 3:
        raise error.TKeyProtocolError('Frame ID must not exceed two bits [0..3]')
    if endpoint > 3:
        raise error.TKeyProtocolError('Frame ID must not exceed two bits [0..3]')
    if cmd.length > 3:
        raise error.TKeyProtocolError('Length value must not exceed two bits [0..3]')

    # Put frame id, endpoint and length in frame header byte
    header = (frame_id << 5) | (endpoint << 3) | cmd.length

    # Lookup command length in bytes from the length bits
    data_length = PROTO_DATA_LENGTH[cmd.length]

    # Create protocol frame with size of header + command length
    frame = bytearray(1 + data_length)

    frame[0] = header  # Set header byte
    frame[1] = cmd.id  # Set command byte

    return frame


def parse_header(header: int) -> Tuple[int, int, int, int]:
    """
    Parse framing protocol header

    """
    frame_id = (header >> 5) & 3
    endpoint = (header >> 3) & 3
    status   = (header >> 2) & 3
    length   = PROTO_DATA_LENGTH[(header & 3)]

    return frame_id, endpoint, status, length


def write_frame(conn: serial.Serial, data: bytes) -> int | None:
    """
    Write data to serial device

    """
    written = 0

    try:
        written = conn.write(data)
    except serial.SerialException as e:
        raise error.TKeyWriteError(e)

    return written


def read_frame(conn: serial.Serial) -> bytes | None:
    """
    Read data from a serial device

    """
    # Attempt to read the response header
    data = bytes()

    try:
        data = conn.read(1)
    except serial.SerialException as e:
        raise error.TKeyReadError(e)

    if len(data) < 1:
        raise error.TKeyReadError('No response data')

    header = data[0]
    frame_id, endpoint, status, length = parse_header(header)

    # If status was NOK, throw away remaining data and raise exception
    if status == 1:
        conn.read_until()
        raise error.TKeyStatusError('Response status code not OK (1)')

    # Read all the remaining data
    data = conn.read_until()

    # Ensure data matches length from header
    if not len(data) == length:
        raise error.TKeyProtocolError('Unexpected response data length')

    response = bytearray(1 + length)

    response[0] = header
    response[1:] = data

    return response


def ensure_frames(command: bytes, response: bytes) -> bool:
    """
    Ensure that a response matches a command, by checking the frame header and
    command ID for both of them.

    """
    cmd_header = parse_header(command[0])
    res_header = parse_header(response[0])

    # Compare frame ID and endpoint
    if not cmd_header[0:2] == res_header[0:2]:
        return False

    # Get command and response ID
    cid = command[1]
    rid = response[1]

    # Compare ID in command and response
    if cid == cmdNameVersion.id:
        if not rid == rspNameVersion.id:
            return False
    elif cid == cmdLoadApp.id:
        if not rid == rspLoadApp.id:
            return False
    elif cid == cmdLoadAppData.id:
        if not rid in [rspLoadAppData.id, rspLoadAppDataReady.id]:
            return False

    return True


def debug_frame(frame: bytes) -> None:
    """
    Print the bytes of a given frame (in binary and hex)

    """
    for i, d in enumerate(frame):
        print('Byte {0}: Binary: {1:b} Hex: 0x{1:x}'.format(i + 1, d))
