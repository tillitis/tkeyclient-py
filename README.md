# Tillitis TKey Python package

This is a Python package for interacting with the Tillitis TKey.

## Purpose

The goal is to implement the TKey protocol, including a small client.

**Update:** As of 2024-05-08, the currently documented TKey protocol has been
implemented.

## TODO

- Actually make this a real package that can be distributed and installed.

## Requirements

This project depends on [pySerial](https://pyserial.readthedocs.io/en/latest/index.html), a package for using serial ports.

## Install

Use pipenv to install the requirements listed in `Pipfile` in a virtual
environment:

```
$ pipenv install
```

Activate the virtual environment to run the client in:

```
$ pipenv shell
```

## Usage

At the moment the package offers a TKey object that can be instantiated by
providing the path to a serial port, with optional baud rate and timeout
settings.

```Python
# Import the package
from tkeyclient.tkey import TKey

# With default baud rate and timeout values
tk = TKey('/dev/ttyACM0')

# With serial connection already opened
tk = TKey('/dev/ttyACM0', connect=True)

# With baud rate set to 9600 bps and timeout set to 5 seconds
tk = TKey('/dev/ttyACM0', speed=9600, timeout=5)

# Open serial connection to device
tk.connect()

# Get device version details
model, name, version = tk.get_name_version()

# Get unique device identifier (UDI)
reserved, vendor, pid, revision, serial = tk.get_udi()

# Get unique device identifier (UDI) as hex string
udi_hex = tk.get_udi_string()

# Load binary application onto device
tk.load_app('blink.bin')

# Load binary application onto device (with user-supplied secret)
tk.load_app('blink.bin', secret='setecastronomy')

# Close serial connection to device
tk.disconnect()
```

### Context management

The `TKey` class can also be used as a context manager, which may be more
convenient as you don't have to open and close the serial connection manually -
it is done by the context manager, even if an exception occurs.

**NOTE:** You need to pass `connection=True` as an argument to automatically
connect, but the connection will always be closed after the context ends.

```Python
# Import the package
from tkeyclient.tkey import TKey

# Create instance within a local context
with TKey('/dev/ttyACM0', connect=True) as tk:

    # Load binary application onto device
    tk.load_app('blink.bin')
```

## Methods

The TKey instance exposes methods that can be used for interacting with the
device:

| Method | Description | Return values |
| :----- | :---------- | :------------ |
| `TKey.connect` | Establish serial connection to device | `None` |
| `TKey.disconnect` | Close serial connection to device | `None` |
| `TKey.test` | Verify that serial port can be opened | `bool` |
| `TKey.get_name_version` | Get device model, name and version | `str, str, int` |
| `TKey.get_udi` | Get unique device identifier (UDI) | `int, int, int, int, int` |
| `TKey.get_udi_string` | Get unique device identifier (UDI) in hex | `str` |
| `TKey.load_app` | Load application onto device | `None` |

## Client

This repository includes a small client which uses the package to interact with
a TKey device:

```
$ python3 ./client.py -h                     
usage: client.py [-h] [-v] [command] ...

Python client for interacting with the Tillitis TKey.

positional arguments:
  [command]
    test         Check if given serial port can be opened
    load         Load application onto device
    version      Get the name and version of stick
    udi          Get the unique device identifier (UDI)

options:
  -h, --help     show this help message and exit
  -v, --verbose

Copyright (c) 2024 Tillitis AB - https://tillitis.se
```

Some commands require an option for the target device. The device can either be
specified manually or found automatically.

Manually:

`$ python3 ./client.py test -d /dev/ttyACM0`

Automatically:

`$ python3 ./client.py test -a`

### Get device model and version

```
$ python3 ./client.py version -d /dev/ttyACM0
2024-05-05 22:14:47,883 - [INFO] cmd: Firmware name0:tk1 name1:mkdf version:5
```

### Get unique device identifier (UDI)

```
$ python3 ./client.py udi -d /dev/ttyACM0
2024-05-08 23:40:26,973 - [INFO] cmd: Got UDI: 0:1337:2:1:00000187
```

### Load application onto device

```
$ python3 ./client.py load -d /dev/ttyACM0 ~/src/tillitis/tkey-testapps/apps/blink/app.bin   
2024-05-05 22:16:09,055 - [INFO] cmd: Application loaded: /home/user/src/tillitis/tkey-testapps/apps/blink/app.bin
```

## Debugging

If the environment variable `TKEY_DEBUG` is set to `1`, data that is sent or
received over the serial port will be printed out in binary and hexadecimal
values:

```
$ TKEY_DEBUG=1 python3 ./client.py load -d /dev/ttyACM0 ~/src/tillitis/tkey-testapps/apps/blink/app.bin 
write_frame(): Sending data:
============================

Byte 001:  01010011  0x53  <- Header
Byte 002:  00000011  0x03  <- Command
Byte 003:  00011110  0x1e  <- Data start
Byte 004:  00000000  0x00
[...]

read_frame(): Received data:
============================

Byte 001:  01010001  0x51  <- Header
Byte 002:  00000100  0x04  <- Response
Byte 003:  00000000  0x00  <- Data start
Byte 004:  00000000  0x00
[...]

write_frame(): Sending data:
============================

Byte 001:  01010011  0x53  <- Header
Byte 002:  00000101  0x05  <- Command
Byte 003:  00110111  0x37  <- Data start
Byte 004:  00000101  0x05
[...]

read_frame(): Received data:
============================

Byte 001:  01010011  0x53  <- Header
Byte 002:  00000111  0x07  <- Response
Byte 003:  00000000  0x00  <- Data start
Byte 004:  10010101  0x95
[...]
```

**NOTE:** The `TKEY_DEBUG` environment variable is used by the protocol library
in this package, not the example client included in the repository. This means
that any application using the package and its protocol implementation can be
debugged in this fashion.

## Disclaimer

This package has been developed and tested using a TKey of the following version:

`Firmware name0:'tk1' name1:'mkdf' version:5`

## Licenses and SPDX tags

Unless otherwise noted, the project sources are licensed under the
terms and conditions of the "GNU General Public License v2.0 only":

> Copyright Tillitis AB.
>
> These programs are free software: you can redistribute it and/or
> modify it under the terms of the GNU General Public License as
> published by the Free Software Foundation, version 2 only.
>
> These programs are distributed in the hope that it will be useful,
> but WITHOUT ANY WARRANTY; without even the implied warranty of
> MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
> General Public License for more details.

> You should have received a copy of the GNU General Public License
> along with this program. If not, see:
>
> https://www.gnu.org/licenses

See [LICENSE](LICENSE) for the full GPLv2-only license text.

External source code we have imported are isolated in their own
directories. They may be released under other licenses. This is noted
with a similar `LICENSE` file in every directory containing imported
sources.

The project uses single-line references to Unique License Identifiers
as defined by the Linux Foundation's [SPDX project](https://spdx.org/)
on its own source files, but not necessarily imported files. The line
in each individual source file identifies the license applicable to
that file.

The current set of valid, predefined SPDX identifiers can be found on
the SPDX License List at:

https://spdx.org/licenses/
