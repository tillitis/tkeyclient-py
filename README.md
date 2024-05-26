# Tillitis TKey Python package

This is a Python package for interacting with the Tillitis TKey.

## Purpose

The goal is to implement the TKey protocol, including a small client that can
be used to do the following:

- Get the name and version
- Load an application (with optional user-supplied secret)

The protocol implementation will start with the parts required to perform the
above, but it may be extended in the future.

## TODO

- Actually make this a real package that can be distributed and installed.
- Implement remaining commands.

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

# With baud rate set to 9600 bps and timeout set to 5 seconds
tk = TKey('/dev/ttyACM0', speed=9600, timeout=5)

# Open serial connection to device
tk.connect()

# Get device version details
model, name, version = tk.get_name_version()

# Load binary application onto device
tk.load_app('blink.bin')

# Load binary application onto device (with user-supplied secret)
tk.load_app('blink.bin', secret='setecastronomy')

# Close serial connection to device
tk.disconnect()
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

options:
  -h, --help     show this help message and exit
  -v, --verbose

Copyright (c) 2024 Tillitis AB - https://tillitis.se
```

### Get device model and version

```
$ python3 ./client.py version /dev/ttyACM0
2024-05-05 22:14:47,883 - [INFO] cmd: Firmware name0:tk1 name1:mkdf version:5
```

### Load application onto device

```
$ python3 ./client.py load /dev/ttyACM0 ~/src/tillitis/tkey-testapps/apps/blink/app.bin   
2024-05-05 22:16:09,055 - [INFO] cmd: Application loaded: /home/user/src/tillitis/tkey-testapps/apps/blink/app.bin
```

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
