# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only
"""Module for low-level interaction with the TKey protocol.

This module includes methods for reading and writing to a TKey device,
including helper methods to create and parse protocol headers and
command/response data.
"""

import os

from collections import namedtuple

import serial

import tkeyclient.error as error


# ID values for firmware/application endpoints
ENDPOINT_FW = 2
ENDPOINT_APP = 3

# Named tuples for command and response frames
fwCommand = namedtuple('fwCommand', ['id', 'length'])
fwCommand.__doc__ = """Representation of a TKey command or response, with protocol ID and maximal data length."""

cmdNameVersion = fwCommand(0x01, 0)
rspNameVersion = fwCommand(0x02, 2)
cmdLoadApp = fwCommand(0x03, 3)
rspLoadApp = fwCommand(0x04, 1)
cmdLoadAppData = fwCommand(0x05, 3)
rspLoadAppData = fwCommand(0x06, 1)
rspLoadAppDataReady = fwCommand(0x07, 3)
cmdGetUDI = fwCommand(0x08, 0)
rspGetUDI = fwCommand(0x09, 2)

# Data lengths for use with command/response frames
PROTO_DATA_LENGTH = [
    1,  # 0
    4,  # 1
    32,  # 2
    128,  # 3
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


def create_frame(
    cmd: fwCommand, frame_id: int, endpoint: int, data: bytes = bytes()
) -> bytearray:
    """Create protocol data structure for a TKey command or response.

    Args:
        cmd: An instance of fwCommand representing the command/response.
        frame_id: Frame ID tag to use in protocol header.
        endpoint: Endpoint number to use in protocol header.
        data: Data to append after protocol header (optional).

    Returns:
        A bytearray object with a valid protocol header and any data passed as
            argument to the function.

    Raises:
        TKeyProtocolError: An invalid value was passed as argument to the function.
    """
    if cmd.id < 0 or cmd.id > 255:
        raise error.TKeyProtocolError('Command ID must not exceed one byte [0..255]')
    if frame_id < 0 or frame_id > 3:
        raise error.TKeyProtocolError('Frame ID must not exceed two bits [0..3]')
    if endpoint < 0 or endpoint > 3:
        raise error.TKeyProtocolError('Frame ID must not exceed two bits [0..3]')
    if cmd.length < 0 or cmd.length > 3:
        raise error.TKeyProtocolError('Length value must not exceed two bits [0..3]')
    if data and len(data) > byte_length(cmd.length):
        raise error.TKeyProtocolError('Data exceeds command data length in header')

    # Put frame id, endpoint and length in frame header byte
    header = (frame_id << 5) | (endpoint << 3) | cmd.length

    # Create protocol frame with size of header + command length
    frame = bytearray(1 + byte_length(cmd.length))

    frame[0] = header  # Set header byte
    frame[1] = cmd.id  # Set command byte

    # Insert command data if provided
    if data:
        frame[2 : 2 + len(data)] = data

    return frame


def parse_header(header: int) -> tuple[int, int, int, int]:
    """Parse protocol header and return field values.

    Args:
        header: The header byte, as an integer

    Returns:
        A tuple with integers representing the following values:

            frame_id    Frame ID tag (0-3)
            endpoint    Endpoint number (0-3)
            status      0 = OK, 1 = Not OK (NOK)
            length      Response data length
    """
    frame_id = (header >> 5) & 3
    endpoint = (header >> 3) & 3
    status = (header >> 2) & 3
    length = header & 3

    return frame_id, endpoint, status, length


def send_command(
    conn: serial.Serial, cmd: fwCommand, eid: int, fid: int, data: bytes = bytes()
):
    """Send a command (with optional data) and return the response.

    This is a high-level function to that handles the framing, command and
    response protocol using the lower-level helper methods for creating,
    writing, reading and validating data.

    Args:
        conn: An instance of a serial.Serial object connected to the device.
        cmd: An instance of fwCommand representing the command to send.
        eid: Endpoint number to use in protocol header.
        fid: Frame ID tag to use in protocol header.
        data: Data to send with the command (optional).

    Raises:
        TKeyProtocolError: Response received did not match the command sent.
    """
    frame = create_frame(cmd, fid, eid, data)

    write_frame(conn, frame)

    response = read_frame(conn)

    if not ensure_frames(frame, response):
        raise error.TKeyProtocolError('Response mismatch')

    return response


def write_frame(conn: serial.Serial, data: bytes) -> int:
    """Write data to the device.

    Args:
        conn: An instance of a serial.Serial object connected to the device.
        data: A byte object with data that should be written to the device.

    Returns:
        Number of bytes written to the device.

    Raises:
        TKeyWriteError: An error occured while writing data to device.
    """
    written = 0

    debug_marks = {0: 'Header'}

    if len(data) > 1:
        debug_marks[1] = 'Command'
    if len(data) > 2:
        debug_marks[2] = 'Data start'

    debug_print(data, header='write_frame(): Sending data:', marks=debug_marks)

    try:
        written = conn.write(data)
        if written is None:
            written = 0
    except serial.SerialException as e:
        raise error.TKeyWriteError(e) from e

    return written


def read_frame(conn: serial.Serial) -> bytes:
    """Read data from the device.

    Args:
        conn: An instance of a serial.Serial object connected to the device.

    Returns:
        A byte object of data that was read from the device.

    Raises:
        TKeyReadError:
            - An error occured while reading data from the device.
            - No response data was returned from device.
        TKeyStatusError: Response status not OK (NOK).
        TKeyProtocolError: Unexpected response data length.
    """
    # Attempt to read the response header
    data = bytes()

    try:
        data = conn.read(1)
    except serial.SerialException as e:
        raise error.TKeyReadError(e) from e

    if len(data) < 1:
        raise error.TKeyReadError('No response data')

    debug_marks = {0: 'Header'}

    header = data[0]
    frame_id, endpoint, status, cmd_len = parse_header(header)
    length = byte_length(cmd_len)

    # If status was NOK, throw away remaining data and raise exception
    if status == 1:
        conn.read(length)
        debug_print(data, header='read_frame(): Received data:', marks=debug_marks)
        raise error.TKeyStatusError('Response status code not OK (1)')

    # Read all the remaining data
    data = conn.read(length)

    if len(data) > 1:
        debug_marks[1] = 'Response'
    if len(data) > 2:
        debug_marks[2] = 'Data start'

    debug_print(
        bytes([header]) + data, header='read_frame(): Received data:', marks=debug_marks
    )

    # Ensure data matches length from header
    if not len(data) == length:
        raise error.TKeyProtocolError('Unexpected response data length')

    response = bytearray(1 + length)

    response[0] = header
    response[1:] = data

    return response


def ensure_frames(command: bytes, response: bytes) -> bool:
    """Ensure that the given response matches the corresponding command.

    This function will compare the header values of a command and response to
    ensure that they match.

    Args:
        command: Data representing the command, as bytes
        response: Data representing the response, as bytes

    Returns:
        True if the command and response headers match, otherwise False.
    """
    cmd_header = parse_header(command[0])
    res_header = parse_header(response[0])

    # Compare frame ID and endpoint
    if cmd_header[0:2] != res_header[0:2]:
        return False

    # Get command and response ID
    cid = command[1]
    rid = response[1]

    # Compare ID in command and response
    if cid == cmdNameVersion.id and rid != rspNameVersion.id:  # noqa: SIM114
        return False
    elif cid == cmdLoadApp.id and rid != rspLoadApp.id:
        return False
    elif cid == cmdLoadAppData.id:
        if rid not in [rspLoadAppData.id, rspLoadAppDataReady.id]:
            return False
    elif cid == cmdGetUDI.id and rid != rspGetUDI.id:
        return False

    return True


def byte_length(index: int) -> int:
    """Return the byte value corresponding to length bit from header.

    Args:
        index: Value of the length bit in header.

    Returns:
        The data size that corresponds to the given bit, in bytes.

    Raises:
        TKeyProtocolError: Length bit value does not conform to protocol.
    """
    if index + 1 > len(PROTO_DATA_LENGTH):
        raise error.TKeyProtocolError('Invalid command length value')

    return PROTO_DATA_LENGTH[index]


def debug_print(frame: bytes, header: str = '', marks: dict | None = None) -> None:
    """Print data if debug mode is enabled, with optional header and markers.

    Args:
        frame: The data to print.
        header: An optional header to show as preface to output.
        marks: An optional dictionary with markers for specific bytes.
    """
    if debug_enabled():
        if header:
            print(header)
            print(('=' * len(header)) + '\n')
        debug_frame(frame, marks=marks)
        print('')


def debug_frame(frame: bytes, marks: dict | None = None) -> None:
    """Print the bytes of a given frame (in binary and hex).

    Args:
        frame: The data to print.
        marks: An optional dictionary with markers for specific bytes.
    """
    for i, d in enumerate(frame):
        # Bytes are 1-indexed for human output, but 0-indexed for everything
        # else (including marks).
        num = i + 1
        if marks and i in marks:
            print(
                'Byte {0:0>3}:  {1:0>8b}  0x{1:0>2x}  <- {2}'.format(
                    num, d, marks.get(i)
                )
            )
        else:
            print('Byte {0:0>3}:  {1:0>8b}  0x{1:0>2x}'.format(num, d))


def debug_enabled() -> bool:
    """Return True if TKEY_DEBUG environment variable is set to 1."""
    return os.getenv('TKEY_DEBUG', None) == '1'
