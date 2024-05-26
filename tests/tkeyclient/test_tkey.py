# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

from unittest.mock import Mock, patch, mock_open

from hashlib import blake2s

import pytest
import serial

import tkeyclient.error as error
import tkeyclient.proto as proto

from tkeyclient.tkey import TKey


def create_mock_serial(handlers={}, **kwargs):
    """
    Create and return a Mock instance of serial.Serial

    """
    mock_serial = Mock(spec=serial.Serial, **kwargs)
    if handlers:
        mock_serial.configure_mock(**handlers)

    return mock_serial


def mock_tkey_conn(file='/dev/ttyDummy0', **kwargs):
    """
    Create a dummy TKey instance with mock serial.Serial

    """
    tkey = TKey(file)

    tkey.conn = create_mock_serial(**kwargs)

    return tkey


def test_connect_success(monkeypatch):
    """
    Assert that connect() opens the serial port

    """
    mock_serial = create_mock_serial()

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'conn', mock_serial)

    tkey.connect()

    mock_serial.open.assert_called_once()


def test_connect_serial_exception(monkeypatch):
    """
    Assert that TKeyConnectionError is raised on serial error during connect

    """
    mock_serial = create_mock_serial(
        {'open.side_effect': serial.SerialException})

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'conn', mock_serial)

    with pytest.raises(error.TKeyConnectionError):
        tkey.connect()

    mock_serial.open.assert_called_once()


def test_connect_invalid_baud_rate_exception():
    """
    Assert that TKeyConfigError is raised on invalid baud rate

    """
    for v in [-1, None]:
        with pytest.raises(error.TKeyConfigError):
            TKey('/dev/ttyDummy0', speed=v)


def test_connect_invalid_timeout_exception():
    """
    Assert that TKeyConfigError is raised on invalid read timeout

    """
    with pytest.raises(error.TKeyConfigError):
        TKey('/dev/ttyDummy0', timeout=-1)


def test_init_autoconnect(monkeypatch):
    """
    Assert that connect() is called upon request when instantiated

    """
    mock = Mock(spec=TKey)

    monkeypatch.setattr(TKey, 'connect', mock.connect)

    TKey('/dev/ttyDummy0', connect=True)

    mock.connect.assert_called_once()


def test_context_opened():
    """
    Assert that requested an instance of TKey is given on context open

    """
    with TKey('/dev/ttyDummy0', speed=1, timeout=2) as tkey:

        assert isinstance(tkey, TKey)

        assert tkey.conn.port == '/dev/ttyDummy0'
        assert tkey.conn.baudrate == 1
        assert tkey.conn.timeout == 2


def test_context_opened_autoconnect(monkeypatch):
    """
    Assert that TKey instance is opened/closed during context

    """
    mock = Mock(spec=TKey)

    mock.test.return_value = True

    monkeypatch.setattr(TKey, 'connect', mock.connect)
    monkeypatch.setattr(TKey, 'disconnect', mock.disconnect)
    monkeypatch.setattr(TKey, 'test', mock.test)

    with TKey('/dev/ttyDummy0', connect=True) as _:
        pass

    mock.connect.assert_called_once()
    mock.disconnect.assert_called_once()
    mock.test.assert_called_once()


def test_serial_close_on_disconnect(monkeypatch):
    """
    Assert that Serial.close() is called by TKey.disconnect()

    """
    mock_serial = create_mock_serial()

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'conn', mock_serial)

    tkey.disconnect()

    mock_serial.close.assert_called_once()


def test_connection_test_opened(monkeypatch):
    """
    Assert that TKey.test() returns True if connection is open

    """
    mock_serial = create_mock_serial(is_open=True)

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'conn', mock_serial)

    assert tkey.test()


def test_connection_test_closed(monkeypatch):
    """
    Assert that TKey.test() returns False if connection is closed

    """
    mock_serial = create_mock_serial(is_open=False)

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'conn', mock_serial)

    assert not tkey.test()


def test_get_name_version_success(monkeypatch):
    """
    Assert that TKey.get_name_version() returns expected values

    """
    data = bytearray()

    data.extend(map(ord, "abcdefgh"))
    data.extend(int.to_bytes(1337, length=4, byteorder='little'))

    response = proto.create_frame(proto.rspNameVersion, 1, 2, data=data)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    name0, name1, version = tkey.get_name_version()

    assert name0 == 'abcd'
    assert name1 == 'efgh'
    assert version == 1337


def test_get_udi_success(monkeypatch):
    """
    Assert that TKey.get_udi() returns expected values

    """
    data = bytearray()

    data.extend([0x00, 0x81, 0x70, 0x33, 0x01, 0x87, 0x01, 0x00])

    response = proto.create_frame(proto.rspGetUDI, 1, 2, data=data)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    reserved, vendor, pid, revision, serial = tkey.get_udi()

    assert reserved == 0x00
    assert vendor == 0x1337
    assert pid == 0x02
    assert revision == 0x01
    assert serial == 0x187


def test_get_udi_string_success(monkeypatch):
    """
    Assert that TKey.get_udi_string() returns expected value

    """
    data = bytearray([0x00, 0x81, 0x70, 0x33, 0x01, 0x87, 0x01, 0x00])

    response = proto.create_frame(proto.rspGetUDI, 1, 2, data=data)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    udi_string = tkey.get_udi_string()

    assert udi_string == '0:1337:2:1:00000187'


@patch('builtins.open', new_callable=mock_open, read_data=b'1337')
def test_get_digest_success(mock):
    """
    Assert that TKey.get_digest() returns expected BLAKE2s digest

    """
    dummy_file = '/tmp/dummy_file'
    length = 32

    tkey = TKey('/dev/ttyDummy0')

    result = tkey.get_digest(dummy_file)

    mock.assert_called_once_with(dummy_file, 'rb')

    expected = blake2s(b'1337', digest_size=length).hexdigest()

    assert len(result) == length
    assert bytes.fromhex(expected) == result


def test_load_app_file_not_found_exception(monkeypatch):
    """
    Assert that TKey.load_app() raises TKeyLoadError for non-existing files

    """
    def file_not_found():
        raise FileNotFoundError()

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'get_digest', file_not_found)

    with pytest.raises(error.TKeyLoadError):
        tkey.load_app('/tmp/dummy_file')


@patch('os.path.getsize')
def test_load_app_file_size_exception(mock_getsize, monkeypatch):
    """
    Assert that TKey.load_app() raises TKeyLoadError for files too large

    """
    mock_getsize.return_value = 1024 * 1024 * 1337
    mock_digest = Mock()

    tkey = TKey('/dev/ttyDummy0')

    monkeypatch.setattr(tkey, 'get_digest', mock_digest)

    with pytest.raises(error.TKeyLoadError):
        tkey.load_app('/tmp/dummy_file')


@patch('os.path.getsize')
@patch('builtins.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_with_user_secret(mock_fopen, mock_getsize, monkeypatch):
    """
    Assert that TKey.load_app() correctly loads the user secret

    """
    secret = 'setecastronomy'

    expected = bytes.fromhex(blake2s(b'1337', digest_size=32).hexdigest())

    mock_getsize.return_value = 30

    response = proto.create_frame(proto.rspLoadApp, 1, 2)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    load_app_data = Mock(return_value=expected)

    monkeypatch.setattr(tkey, 'load_app_data', load_app_data)

    tkey.load_app('/tmp/dummy_file', secret=secret)

    data = send_command.call_args.args[4]

    secret_data = data[5:][:len(secret)]

    assert len(data) == 127
    assert secret == bytes(secret_data).decode('utf-8')


@patch('os.path.getsize')
@patch('builtins.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_bad_status(mock_fopen, mock_getsize, monkeypatch):
    """
    Assert that TKey.load_app() raises TKeyLoadError on status NOK

    """
    mock_getsize.return_value = 30

    response = proto.create_frame(proto.rspLoadApp, 1, 2)

    response[2] = 1  # set STATUS_BAD for FW_RSP_LOAD_APP (0x04)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    with pytest.raises(error.TKeyLoadError):
        tkey.load_app('/tmp/dummy_file')


@patch('os.path.getsize')
@patch('builtins.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_compare_hash_success(mock_fopen, mock_getsize, monkeypatch):
    """
    Assert that TKey.load_app() compare the source and result hashes

    """
    mock_getsize.return_value = 30

    expected = bytes.fromhex(blake2s(b'1337', digest_size=32).hexdigest())

    response = proto.create_frame(proto.rspLoadApp, 1, 2)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    load_app_data = Mock(return_value=expected)

    monkeypatch.setattr(tkey, 'load_app_data', load_app_data)

    tkey.load_app('/tmp/dummy_file')


@patch('os.path.getsize')
@patch('builtins.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_compare_hash_failed(mock_fopen, mock_getsize, monkeypatch):
    """
    Assert that TKey.load_app() compare the source and result hashes

    """
    wrong_value = b'1234'

    mock_getsize.return_value = 30

    wrong = bytes.fromhex(blake2s(wrong_value, digest_size=32).hexdigest())

    response = proto.create_frame(proto.rspLoadApp, 1, 2)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    load_app_data = Mock(return_value=wrong)

    monkeypatch.setattr(tkey, 'load_app_data', load_app_data)

    with pytest.raises(error.TKeyLoadError):
        tkey.load_app('/tmp/dummy_file')


@patch('io.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_data_done_success(mock_fopen, monkeypatch):
    """
    Assert that load_app() raises TKeyProtocolError on unexpected response code

    """
    expected = bytes.fromhex(blake2s(b'1337', digest_size=32).hexdigest())

    response = proto.create_frame(proto.rspLoadAppDataReady, 1, 2)

    response[3:3 + 32] = expected

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    digest = tkey.load_app_data(4, '/tmp/dummy_file')

    assert digest == expected


@patch('io.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_data_bad_status(mock_fopen, monkeypatch):
    """
    Assert that load_app() raises TKeyProtocolError on unexpected response code

    """
    response = proto.create_frame(proto.rspLoadAppDataReady, 1, 2)

    response[2] = 1  # set STATUS_BAD for FW_RSP_LOAD_APP_DATA (0x06)

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    with pytest.raises(error.TKeyLoadError):
        tkey.load_app_data(4, '/tmp/dummy_file')


@patch('io.open', new_callable=mock_open, read_data=b'1337')
def test_load_app_data_unexpected_response(mock_fopen, monkeypatch):
    """
    Assert that load_app() throws error on unexpected response code

    """
    response = proto.create_frame(proto.rspLoadAppData, 1, 2)

    response[1] = 0x99  # set unknown response code

    send_command = Mock(return_value=response)

    monkeypatch.setattr(proto, 'send_command', send_command)

    tkey = TKey('/dev/ttyDummy0')

    with pytest.raises(error.TKeyProtocolError):
        tkey.load_app_data(4, '/tmp/dummy_file')
