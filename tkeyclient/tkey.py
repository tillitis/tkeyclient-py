# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only
"""High-level module for interacting with the TKey device.

This module exports a TKey class with methods for commands supported by the
device.
"""

import io
import os
import serial

from hashlib import blake2s

import tkeyclient.error as error
import tkeyclient.proto as proto


# Defaults for serial communication with the TKey
DEFAULT_SPEED: int = 62500
DEFAULT_TIMEOUT: int = 1

# Max size for applications to load onto TKey
APP_MAXSIZE: int = 100 * 1024


class TKey:
    """Class implementation of a TKey.

    An instance of this class represents a TKey device, with methods that
    corresponds to the commands supported by the TKey.
    """

    conn: serial.Serial

    def __init__(
        self,
        device: str,
        speed: int = DEFAULT_SPEED,
        timeout: int = DEFAULT_TIMEOUT,
        connect: bool = False,
    ):
        """Create new instance of a TKey device.

        Args:
            device: Path to the TKey serial device
            speed: Baud rate to use for serial communication
            timeout: Timeout for reading from serial port
            connect: If True automatically connect to device

        Raises:
            TKeyConfigError: If serial device parameters are invalid.

        Warning: Connection
            By default, the connection to the TKey device will not be opened upon
            creating an instance. Use the `connect()` method after creating the
            instance, or pass `connect=True` as an argument when creating the
            instance.

        Examples:
            >>> import tkeyclient.tkey as TKey
            >>> tkey = TKey('/dev/ttyACM0')
            >>> tkey.connect()
            >>> tkey.test()
            True
            >>> tkey.get_udi_string()
            '0:1337:2:1:00000042'

            >>> import tkeyclient.tkey as TKey
            >>> with TKey('/dev/ttyACM0', connect=True) as tkey:
            ...     # In context, test if connected
            ...     tkey.test()
            ...     tkey.get_name_version()
            ...
            True
            ('tk1', 'mkdf', 5)
            >>> # No longer in context, test if connected
            >>> tkey.test()
            False
        """
        self.conn = serial.Serial()

        try:
            self.conn.port = device
            self.conn.baudrate = speed
            self.conn.timeout = timeout
        except ValueError as e:
            raise error.TKeyConfigError(e) from e

        # Open serial port if requested
        if connect:
            self.connect()

    def __enter__(self):
        """Entry point for a TKey context manager."""
        return self

    def __exit__(self, type, value, traceback):
        """Exit point for a TKey context manager."""
        # Close serial port if opened
        if self.test():
            self.disconnect()

        return False

    def __repr__(self):
        """Get string representation of current instance.

        Returns:
            A string with the Python expression required for recreating current instance.
        """
        return "{0}('{1}', speed={2}, timeout={3})".format(
            type(self).__name__, self.conn.port, self.conn.baudrate, self.conn.timeout
        )

    def connect(self) -> None:
        """Open serial connection to device.

        Raises:
            TKeyConnectionError: If connection cannot be opened.
        """
        try:
            self.conn.open()
        except serial.SerialException as e:
            raise error.TKeyConnectionError(e) from e

    def disconnect(self) -> None:
        """Close serial connection to device."""
        self.conn.close()

    def test(self) -> bool:
        """Test if device is connected.

        Returns:
            True if serial connection to device is currently open.

        Examples:
            >>> tkey = TKey('/dev/ttyACM0')
            >>> tkey.connect()
            >>> tkey.test()
            True
            >>> tkey.disconnect()
            >>> tkey.test()
            False
        """
        return self.conn.is_open

    def get_name_version(self) -> tuple[str, str, int]:
        """Retrieve name and version of the device and firmware.

        Returns:
            Device model
            Firmware name
            Firmware version

        Examples:
            >>> tkey.get_name_version()
            ('tk1', 'mkdf', 5)
        """
        response = proto.send_command(
            self.conn, proto.cmdNameVersion, proto.ENDPOINT_FW, 2
        )

        data = response[2:]

        name0 = data[0:][:4].decode('ascii').rstrip()
        name1 = data[4:][:4].decode('ascii').rstrip()

        version = int.from_bytes(data[8:][:4], byteorder='little')

        return name0, name1, version

    # Data structure for FW_RSP_GET_UDI (0x09)
    # ========================================
    #
    # Reserved           4 bits
    # Vendor             1 byte
    # Product ID         6 bits
    # Product revision   6 bits
    # Serial number      2 bytes
    #
    # Total              4 bytes (32 bits)

    def get_udi(self) -> tuple[int, int, int, int, int]:
        """Retrieve unique device identifier (UDI) of the device.

        These values can be used to uniquely identify a specific TKey. They are
        returned as integers but they make more sense in hexadecimal notation.
        Use the `get_udi_string` method to get a hexadecimal string with these
        details concatenated in a more useful format.

        Returns:
            Reserved (unused)
            Vendor ID
            Product ID
            Product revision
            Serial number

        Examples:
            >>> tkey.get_udi()
            (0, 4919, 2, 1, 391)
        """
        response = proto.send_command(self.conn, proto.cmdGetUDI, proto.ENDPOINT_FW, 2)

        data = response[3:]

        # Get device vendor and product details
        product = int.from_bytes(data[0:4], byteorder='little')

        reserved = (product >> 28) & 15
        vendor = (product >> 12) & 65535
        pid = (product >> 6) & 63
        revision = product & 63

        # Get device serial number
        serial = int.from_bytes(data[4:8], byteorder='little')

        return reserved, vendor, pid, revision, serial

    def get_udi_string(self) -> str:
        """Retrieve unique device identifier (UDI) as a hexadecimal string.

        This will return the UDI in a more useful format if you need to get an
        unique value representing the TKey device. It concatenates the values
        from `get_udi` into a string with hexadecimal values, separated by
        colon.

        Returns:
            A string with hexadecimal values of the UDI for the device.

        Examples:
            >>> tkey.get_udi_string()
            '0:1337:2:1:00000042'
        """
        reserved, vendor, pid, revision, serial = self.get_udi()
        return '{0:01x}:{1:04x}:{2:x}:{3:x}:{4:08x}'.format(
            reserved, vendor, pid, revision, serial
        )

    def load_app(self, file: str, secret: str | None = None) -> None:
        """Load an application onto the device.

        Args:
            file: Path to a binary file to load.
            secret: A user-supplied secret (USS) to send with the binary.

        Raises:
            TKeyLoadError:
                - If the binary cannot be found/read.
                - If the binary is too big (size > APP_MAXSIZE)
                - If the device is not ready to load an application.
                - If the BLAKE2s-256s digest of application received by device does not match the source binary.
        """
        # Calculate size and BLAKE2s digest from source file
        try:
            file_size = os.path.getsize(file)
            file_digest = self._get_digest(file)
        except FileNotFoundError as e:
            raise error.TKeyLoadError(e) from e

        # Ensure file size is not bigger than max allowed
        if file_size > APP_MAXSIZE:
            raise error.TKeyLoadError(
                'File too big (%d > %d)' % (file_size, APP_MAXSIZE)
            )

        # Initialize command data
        data = bytearray(127)

        # Set size for application payload (4 bytes, little endian)
        size_bytes = int(file_size).to_bytes(4, byteorder='little')
        data[0] = size_bytes[0]
        data[1] = size_bytes[1]
        data[2] = size_bytes[2]
        data[3] = size_bytes[3]

        # Handle user-supplied secret if provided
        data[4] = 0
        if secret is not None:
            data[4] = 1
            data[5 : 5 + len(secret)] = bytes(secret, encoding='utf8')

        response = proto.send_command(
            self.conn, proto.cmdLoadApp, proto.ENDPOINT_FW, 2, data
        )

        load_status = response[2]
        if load_status == 1:
            raise error.TKeyLoadError('Device not ready (1 = STATUS_BAD)')

        # Upload application data to device and get BLAKE2s digest
        result_digest = self._load_app_data(file_size, file)

        # Compare application hashes
        if not file_digest == result_digest:
            raise error.TKeyLoadError(
                'Hash digests do not match (%s != %s)'
                % (file_digest.hex(), result_digest.hex())
            )

    def _load_app_data(self, file_size: int, file: str) -> bytes:
        """Load application data onto the device and return BLAKE2s-256 hash digest.

        For internal use by the `load_app` method.

        Used for splitting the source binary into 127-byte chunks and send them
        over to the device.

        Args:
            file_size: Size of the source binary to load, in bytes.
            file: Path of the source binary to load.

        Returns:
            Byte representation of a 32-byte BLAKE2s-256 hash digest for the
                application actually received by the device.

        Raises:
            TKeyLoadError: If an error was encountered when loading application.
            TKeyProtocolError: If unexpected data was received from device.
        """
        dataframes = []

        with io.open(file, 'rb') as f:
            bytes_read = 0
            while bytes_read < file_size:
                data = f.read(127)
                dataframes.append(data)
                bytes_read += len(data)

        digest = bytearray(32)

        for df in dataframes:
            response = proto.send_command(
                self.conn, proto.cmdLoadAppData, proto.ENDPOINT_FW, 2, df
            )

            response_id, status = response[1:3]
            if status == 1:
                raise error.TKeyLoadError('Bad status when writing (1 = STATUS_BAD)')

            if response_id == proto.rspLoadAppDataReady.id:
                digest = bytearray(response[3:][:32])
            elif response_id != proto.rspLoadAppData.id:
                raise error.TKeyProtocolError(
                    'Unexpected response code (%d)' % response_id
                )

        return bytes(digest)

    def _get_digest(self, file) -> bytes:
        """Return BLAKE2s-256 digest for given file as bytes.

        Args:
            file: Path of a file for which to calculate the BLAKE2s-256 hash digest.

        Returns:
            Byte representation of a 32-byte BLAKE2s-256 hash digest for the
                file passed as argument to this function.
        """
        with open(file, 'rb') as f:
            data = f.read()
        return bytes.fromhex(blake2s(data, digest_size=32).hexdigest())
