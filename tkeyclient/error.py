# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

class TKeyError(Exception):
    pass

class TKeyConnectionError(TKeyError):
    pass

class TKeyWriteError(TKeyError):
    pass

class TKeyReadError(TKeyError):
    pass

class TKeyStatusError(TKeyError):
    pass

class TKeyProtocolError(TKeyError):
    pass

class TKeyLoadError(TKeyError):
    pass

class TKeyDeviceError(TKeyError):
    pass
