# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

import pytest

from unittest.mock import Mock

import serial

import tkeyclient.error as error
import tkeyclient.proto as proto


command_map = [
    (proto.cmdNameVersion, proto.rspNameVersion),
    (proto.cmdLoadApp,     proto.rspLoadApp),
    (proto.cmdLoadAppData, proto.rspLoadAppData),
    (proto.cmdLoadAppData, proto.rspLoadAppDataReady),
    (proto.cmdGetUDI,      proto.rspGetUDI),
]


def create_mock_serial(handlers={}, **kwargs):
    """
    Create and return a Mock instance of serial.Serial

    """
    mock_serial = Mock(spec=serial.Serial, **kwargs)
    if handlers:
        mock_serial.configure_mock(**handlers)

    return mock_serial


def test_proto_data_length_exists():
    """
    Assert that PROTO_DATA_LENGTH exists and is a list

    """
    assert proto.PROTO_DATA_LENGTH and isinstance(proto.PROTO_DATA_LENGTH, list)


def test_create_frame_valid_header():
    """
    Assert that create_frame() returns a valid header + command byte

    """
    header = proto.create_frame(proto.cmdNameVersion, 1, 2)

    assert header[0] == 0x30
    assert header[1] == proto.cmdNameVersion.id


def test_create_frame_header_with_data():
    """
    Assert that create_frame() returns frame with data

    """
    data = bytes([1, 2, 3, 4])
    header = proto.create_frame(proto.cmdLoadApp, 1, 2, data=data)

    assert header[2:6] == data


def test_create_frame_invalid_command_id():
    """
    Assert that create_frame() validates command ID

    """
    for command_id in [ 1337, -1 ]:
        with pytest.raises(error.TKeyProtocolError):
            testCommand = proto.fwCommand(command_id, 1)
            proto.create_frame(testCommand, 1, 2)


def test_create_frame_invalid_frame_id():
    """
    Assert that create_frame() validates frame ID

    """
    for endpoint in [ 1337, -1 ]:
        with pytest.raises(error.TKeyProtocolError):
            proto.create_frame(proto.cmdNameVersion, endpoint, 2)


def test_create_frame_invalid_endpoint_id():
    """
    Assert that create_frame() validates endpoint ID

    """
    for frame_id in [ 1337, -1 ]:
        with pytest.raises(error.TKeyProtocolError):
            proto.create_frame(proto.cmdNameVersion, 1, frame_id)


def test_create_frame_invalid_command_length():
    """
    Assert that create_frame() validates command length bit

    """
    for cmd_length in [ 1337, -1 ]:
        testCommand = proto.fwCommand(0x01, cmd_length)
        with pytest.raises(error.TKeyProtocolError):
            proto.create_frame(testCommand, 1, 2)


def test_create_frame_command_data_more_than_length_bit():
    """
    Assert that create_frame() validates size of data in args

    """
    data = bytes([1, 2, 3, 4])
    testCommand = proto.fwCommand(0x01, 0)
    with pytest.raises(error.TKeyProtocolError):
        proto.create_frame(testCommand, 1, 2, data=data)


def test_parse_header_valid_result():
    """
    Assert that parse_header() returns valid result

    """
    frame_id, endpoint, status, length = proto.parse_header(0b00110100)

    assert frame_id == 1
    assert endpoint == 2
    assert status == 1
    assert length == proto.cmdNameVersion.length


def test_byte_value_valid_size():
    """
    Assert that byte_header() returns valid byte length

    """
    for i, length in enumerate(proto.PROTO_DATA_LENGTH):
        assert proto.byte_length(i) == length


def test_byte_value_invalid_size():
    """
    Assert that byte_header() raises exception for invalid lengths

    """
    with pytest.raises(error.TKeyProtocolError):
        proto.byte_length(len(proto.PROTO_DATA_LENGTH) + 1)


def test_ensure_frame_compare_valid_command_response():
    """
    Assert that comparison between command and response ID is valid

    """
    for u in command_map:

        command, response = u

        cmd = proto.create_frame(command, 1, 2)
        rsp = bytearray(cmd)

        # Set status flag and response ID
        rsp[0] |= 1 << 2
        rsp[1] = response.id

        assert proto.ensure_frames(cmd, rsp)


def test_ensure_frame_compare_wrong_response():
    """
    Assert comparison between command and wrong response ID

    """
    for u in command_map:

        command, _ = u

        cmd = proto.create_frame(command, 1, 2)
        rsp = bytearray(cmd)

        # Set status flag and response ID
        rsp[1] = 0x99

        assert not proto.ensure_frames(cmd, rsp)


def test_ensure_frame_compare_wrong_frame_id():
    """
    Assert comparison between command and response frame ID

    """
    command = proto.create_frame(proto.cmdNameVersion, 1, 2)
    response = bytearray(command)

    # Set wrong frame ID and valid response ID
    response[0] |= 2 << 5
    response[1] = 0x02

    assert not proto.ensure_frames(command, response)


def test_ensure_frame_compare_wrong_endpoint():
    """
    Assert comparison between command and response endpoint

    """
    command = proto.create_frame(proto.cmdNameVersion, 1, 2)
    response = bytearray(command)

    # Set wrong frame ID and valid response ID
    response[0] |= 1 << 3
    response[1] = 0x02

    assert not proto.ensure_frames(command, response)


def test_write_frame_serial_exception():
    """
    Assert TKeyWriteError on serial.SerialException in write_frame()

    """
    mock_serial = create_mock_serial()
    mock_serial.write.side_effect = serial.SerialException

    with pytest.raises(error.TKeyWriteError):
        proto.write_frame(mock_serial, bytes())

    mock_serial.write.assert_called_once()

    
def test_write_frame_bytes_written():
    """
    Assert successful writing to serial device, 1337 bytes

    """
    mock_serial = create_mock_serial()
    mock_serial.write.return_value = 1337

    assert proto.write_frame(mock_serial, bytes()) == 1337

    mock_serial.write.assert_called_once()


def test_write_frame_no_bytes_written():
    """
    Assert successful writing to serial device, None bytes

    """
    mock_serial = create_mock_serial()
    mock_serial.write.return_value = None

    assert proto.write_frame(mock_serial, bytes()) == 0

    mock_serial.write.assert_called_once()


def test_write_frame_debug_default_marks(monkeypatch):
    """
    Assert that all default debug marks are set by write_frame()

    """
    mock = Mock()
    monkeypatch.setattr(proto, 'debug_print', mock.debug_print)

    mock_serial = create_mock_serial()
    proto.write_frame(mock_serial, bytes([0x00, 0x01, 0x13, 0x37]))

    mock.debug_print.assert_called_once()

    kwargs = mock.debug_print.call_args.kwargs

    assert 'marks' in kwargs.keys()

    debug_marks = kwargs.get('marks')

    assert debug_marks.get(0) == 'Header'
    assert debug_marks.get(1) == 'Command'
    assert debug_marks.get(2) == 'Data start'


def test_read_frame_serial_exception():
    """
    Assert exception on no response data

    """
    mock_serial = create_mock_serial()
    mock_serial.read.side_effect = serial.SerialException

    with pytest.raises(error.TKeyReadError):
        proto.read_frame(mock_serial)

    mock_serial.read.assert_called_once()


def test_read_frame_no_response_data():
    """
    Assert exception on no response data

    """
    mock_serial = create_mock_serial()
    mock_serial.read.return_value = bytes()

    with pytest.raises(error.TKeyReadError):
        proto.read_frame(mock_serial)

    mock_serial.read.assert_called_once()


def test_read_frame_status_nok():
    """
    Assert exception on no response data

    """
    header = 0x00 | 1 << 2  # set status NOK

    mock_serial = create_mock_serial()
    mock_serial.read.return_value = bytes([header])

    with pytest.raises(error.TKeyStatusError):
        proto.read_frame(mock_serial)

    mock_serial.read.assert_called()


def test_read_frame_expected_data_length():
    """
    Assert expected response data length

    """
    header = 0x00 | 3  # set command data length to 128 bytes
    data = bytes([header, 0x07, 0x00]) + bytearray(126)

    mock_serial = create_mock_serial()
    mock_serial.read.side_effect = [ bytes([header]), bytes(data[1:]) ]

    response = proto.read_frame(mock_serial)

    assert len(response[1:]) == len(data[1:])

    mock_serial.read.assert_called()


def test_read_frame_invalid_data_length(monkeypatch):
    """
    Assert that read_frame() raises exception for invalid command lengths

    """
    parse_header = Mock(return_value=(0, 0, 0, 1))

    monkeypatch.setattr(proto, "parse_header", parse_header)

    header = 0x00 | 0  # set command data length to 1 byte
    data = bytes([header, 0x07])

    mock_serial = create_mock_serial()
    mock_serial.read.side_effect = [ bytes([header]), bytes(data[1:]) ]

    with pytest.raises(error.TKeyProtocolError):
        proto.read_frame(mock_serial)


def test_read_frame_debug_default_marks(monkeypatch):
    """
    Assert that all default debug marks are set by read_frame()

    """
    header = 0x00 | 1 << 5 | 2 << 3 | 0 << 2 | 1
    data = [ 0x02, 0x13, 0x33, 0x37 ]

    mock = Mock()
    monkeypatch.setattr(proto, 'debug_print', mock.debug_print)

    mock_serial = create_mock_serial()
    mock_serial.read.side_effect = [ bytes([header]), bytes(data) ]

    proto.read_frame(mock_serial)

    mock_serial.read.assert_called()
    mock.debug_print.assert_called_once()

    kwargs = mock.debug_print.call_args.kwargs

    assert 'marks' in kwargs.keys()

    debug_marks = kwargs.get('marks')

    assert len(debug_marks) == 3

    assert debug_marks.get(0) == 'Header'
    assert debug_marks.get(1) == 'Response'
    assert debug_marks.get(2) == 'Data start'


def test_send_command_unexpected_response():
    """
    Assert unexpected response code

    """
    header = 0x00 | 1 << 3  # set endpoint ID

    mock_serial = create_mock_serial()
    mock_serial.read.side_effect = [ bytes([header]), bytes([0x01]) ]

    with pytest.raises(error.TKeyProtocolError):
        proto.send_command(mock_serial, proto.cmdNameVersion, 2, 0)

    mock_serial.read.assert_called()


def test_send_command_expected_response():
    """
    Assert unexpected response

    """
    header = 0x00 | 1 << 5 | 2 << 3 | 0 << 2 # set frame ID, endpoint and status

    mock_serial = create_mock_serial()
    mock_serial.read.side_effect = [
        bytes([header]), bytes([proto.rspNameVersion.id])
    ]

    proto.send_command(mock_serial, proto.cmdNameVersion, 2, 1)

    mock_serial.read.assert_called()


def test_debug_print(monkeypatch):
    """
    Assert that debug_frame() is called with expected arguments

    """
    mock = Mock()

    monkeypatch.setenv('TKEY_DEBUG', '1')
    monkeypatch.setattr(proto, 'debug_frame', mock.debug_frame)

    proto.debug_print(bytes([0x13, 0x33, 0x37]), header='header', marks={0: 'a'})

    mock.debug_frame.assert_called_once()

    args = mock.debug_frame.call_args.args
    kwargs = mock.debug_frame.call_args.kwargs

    assert args[0] == bytes([0x13, 0x33, 0x37])
    assert kwargs == { 'marks': { 0: 'a' } }


def test_debug_frame_without_mark(capsys):
    """
    Assert that debug_frame() produces expected text without mark

    """
    proto.debug_frame(bytes([0x13]))
    capture = capsys.readouterr()

    assert capture.out == 'Byte 001:  00010011  0x13\n'


def test_debug_frame_with_mark(capsys):
    """
    Assert that debug_frame() produces expected text with mark

    """
    proto.debug_frame(bytes([0x13]), marks={0: 'a'})
    capture = capsys.readouterr()

    assert capture.out == 'Byte 001:  00010011  0x13  <- a\n'
