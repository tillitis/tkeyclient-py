# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only
"""Exceptions raised by the tkeyclient package."""

# fmt: off

class TKeyError(Exception):
    """Base class for exceptions raised by package."""
    pass

class TKeyConnectionError(TKeyError):
    """Raised when a serial connection cannot be opened."""
    pass

class TKeyWriteError(TKeyError):
    """Raised when data cannot be written to device."""
    pass

class TKeyReadError(TKeyError):
    """Raised when data cannot be read from device."""
    pass

class TKeyStatusError(TKeyError):
    """Raised when response status is not OK (NOK)."""
    pass

class TKeyProtocolError(TKeyError):
    """Raised upon protocol errors in command or response."""
    pass

class TKeyLoadError(TKeyError):
    """Raised if device failed to load application."""
    pass

class TKeyDeviceError(TKeyError):
    """Raised if device could not be found."""
    pass

class TKeyConfigError(TKeyError):
    """Raised if device configuration is invalid."""
    pass

# fmt: on
