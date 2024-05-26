# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

from unittest.mock import Mock

import pytest

from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

import tkeyclient.error as error
import tkeyclient.hw as hw


def create_tkey(path='/dev/ttyTkey0'):
    """
    Create ListPortInfo instance representing a TKey device

    """
    tkey = ListPortInfo(device=path)
    tkey.vid = hw.USB_VID
    tkey.pid = hw.USB_PID

    return tkey


def test_find_device_exception(monkeypatch):
    """
    Assert that not finding a device raises exception

    """
    empty_list = Mock(return_value=[])

    monkeypatch.setattr(hw, 'list_devices', empty_list)

    with pytest.raises(error.TKeyDeviceError):
        hw.find_device()


def test_find_device_success(monkeypatch):
    """
    Assert finding a device

    """
    list_one = Mock(return_value=[ListPortInfo(device='/dev/ttyDummy0')])

    monkeypatch.setattr(hw, 'list_devices', list_one)

    assert type(hw.find_device()) == ListPortInfo


def test_filter_tkey_devices(monkeypatch):
    """
    Assert finding multiple TKey devices

    """
    multiple_devices = Mock(
        return_value=[
            ListPortInfo(device='/dev/ttyDummy0'),
            create_tkey('/dev/ttyTkey2'),
            create_tkey('/dev/ttyTkey10'),
        ]
    )

    monkeypatch.setattr(list_ports, 'comports', multiple_devices)

    assert len(hw.list_devices()) == 2


def test_sort_tkey_devices(monkeypatch):
    """
    Assert sorting devices by natural sorting of numbers

    """
    multiple_devices = Mock(
        return_value=[
            create_tkey('/dev/ttyTkey10'),
            create_tkey('/dev/ttyTkey2'),
        ]
    )

    monkeypatch.setattr(list_ports, 'comports', multiple_devices)

    result = hw.list_devices()

    assert result[0].device == '/dev/ttyTkey2'
