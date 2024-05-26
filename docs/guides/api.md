# Using the TKey API

Here you can find some examples on how to use the [TKey API](../reference/tkeyclient/tkey.md/) to interact with a TKey device from your own Python applications or packages.

## TKey instances

An instance object of the `TKey` class represents a TKey device connected to your system.

You can create multiple instances for multiple devices if needed.

There are two ways to get an instance; use the class constructor or the context manager.

!!! Warning "Connection"
    By default, the connection to the TKey device will not be opened upon
    creating an instance. Use the `connect()` method after creating the
    instance, or pass `connect=True` as an argument when creating the
    instance.

### Using the constructor

``` python
from tkeyclient.tkey import TKey
tkey = TKey('/dev/ttyACM0')
# Your code here ...
```

### Using the context manager

``` python
from tkeyclient.tkey import TKey
with TKey('/dev/ttyACM0') as tkey:
    # Your code here ...
```

The `TKey` context manager works the same way as the builtin `with open(...) as
f:` for working with file objects in Python.

When using the context manager as above, the `tkey` instance will be usable as
long as the context lasts. Any open connection to the TKey device will be
closed when the context is closed.

## Supported commands

### Get version information

To fetch the model and firmware version of a TKey device connected to the
system, you can use the [`get_name_version`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.get_name_version) method on a TKey instance:

``` python
from tkeyclient.tkey import TKey
tkey = TKey('/dev/ttyACM0', connect=True)
tkey.get_name_version()
('tk1', 'mkdf', 5)
```

Official developer documentation for this command is available [here](https://dev.tillitis.se/protocol/#fw_cmd_name_version-0x01).

### Get unique device identifier (UDI)

To fetch the unique device identifier (UDI) string of a TKey device, you can
use the [`get_udi`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.get_udi) or [`get_udi_string`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.get_udi_string) methods on a TKey instance:

``` python
from tkeyclient.tkey import TKey
tkey = TKey('/dev/ttyACM0', connect=True)

tkey.get_udi()        # (0, 4919, 2, 1, 391)
tkey.get_udi_string() # '0:1337:2:1:00000042'
```

[`get_udi`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.get_udi) will return a tuple with integer values and [`get_udi_string`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.get_udi_string) will return a string with the same values in hexadecimal notation, separated by colons.

Official developer documentation for this command is available [here](https://dev.tillitis.se/protocol/#fw_cmd_get_udi-0x08).

### Load application onto device

To upload an application to the device, you can use the [`load_app`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.load_app) method on a
TKey instance with the file path to the binary as an argument:

``` python
from tkeyclient.tkey import TKey
tkey = TKey('/dev/ttyACM0', connect=True)
tkey.load_app('/home/user/blink.bin')
```

In the example above, `/home/user/blink.bin` is an application in form of a
binary that will be sent to and loaded by the device.

**NOTE:** The binary size may not exceed 100 kilobytes.

Official developer documentation for this command is available [here](https://dev.tillitis.se/protocol/#fw_cmd_load_app-0x03).

#### With user-supplied secret (USS)

When loading an application onto the device, you can send a user-supplied
secret (USS) as the second argument to the [`load_app`](../reference/tkeyclient/tkey.md/#tkeyclient.tkey.TKey.load_app) method:

``` python
tkey.load_app('/home/user/blink.bin', 'setecastronomy')
```

In the example above, `setecastronomy` is the user-supplied secret that will be
included with the application being sent to the device.

**NOTE:** The secret may not exceed 32 characters (bytes).
