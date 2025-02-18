# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only
"""Helpers for listing and identifying connected TKey devices.

This module includes helper methods that can be used to list TKey devices
currently connected to the system.
"""
from typing import List

from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo

from tkeyclient.error import TKeyDeviceError


# TKey USB device ID (vendor and product)
USB_VID = 0x1207
USB_PID = 0x8887


def find_device() -> ListPortInfo:
    """Return the first usable TKey device found.

    Will raise a `TKeyDeviceError` exception if no device was found.

    Returns:
        An instance of `serial.ListPortInfo` for the first TKey found.

    Raises:
        TKeyDeviceError: No TKey devices were found
    """
    devices = list_devices()
    if not devices:
        raise TKeyDeviceError('No usable device found')

    return devices[0]


def list_devices() -> List[ListPortInfo]:
    """Return a list with serial device info for all TKeys connected.

    Returns:
        A list of `serial.ListPortInfo` instances for all TKey devices found.
    """
    return sorted(filter(filter_device, list_ports.comports()))


def filter_device(d: ListPortInfo) -> bool:
    """Return `True` if serial port belongs to a TKey device.

    Args:
        d: An instance of `serial.ListPortInfo`

    Returns:
        `True` if the `serial.ListPortInfo` instance represents a TKey device.
    """
    return d.vid == USB_VID and d.pid == USB_PID
