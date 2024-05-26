# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

from typing import Tuple

import io
import os
import serial

from hashlib import blake2s

import tkeyclient.error as error
import tkeyclient.proto as proto


# Defaults for serial communication with the TKey
DEFAULT_SPEED = 62500
DEFAULT_TIMEOUT = 1
APP_MAXSIZE = 100 * 1024

class TKey:

    conn: serial.Serial

    def __init__(self, device, speed=DEFAULT_SPEED, timeout=DEFAULT_TIMEOUT, connect=False):
        """
        Create new instance of a TKey object

        Raises:
            TKeyConfigError: If serial device parameters are invalid.
        """
        self.conn = serial.Serial()

        try:
            self.conn.port = device
            self.conn.baudrate = speed
            self.conn.timeout = timeout
        except ValueError as e:
            raise error.TKeyConfigError(e)

        # Open serial port if requested
        if connect == True:
            self.connect()


    def __enter__(self):
        """
        Entry point for a TKey context manager

        """
        return self


    def __exit__(self, type, value, traceback):
        """
        Exit point for a TKey context manager

        """
        # Close serial port if opened
        if self.test():
            self.disconnect()

        return False


    def connect(self) -> None:
        """
        Open connection to the given serial device

        Raises:
            TKeyConnectionError: If serial device cannot be opened.
        """
        try:
            self.conn.open()
        except serial.SerialException as e:
            raise error.TKeyConnectionError(e)


    def disconnect(self) -> None:
        """
        Close connection to the serial device

        """
        self.conn.close()


    def test(self) -> bool:
        """
        Test if serial connection is open

        """
        return self.conn.is_open


    def get_name_version(self) -> Tuple[str, str, int]:
        """
        Retrieve name and version of the device

        """
        response = proto.send_command(
            self.conn, proto.cmdNameVersion, proto.ENDPOINT_FW, 2)

        data = response[2:]

        name0 = data[0:][:4].decode('ascii').rstrip()
        name1 = data[4:][:4].decode('ascii').rstrip()

        version = int.from_bytes(data[8:][:4], byteorder='little')

        return name0, name1, version


    def get_udi(self) -> Tuple[int, int, int, int, int]:
        """
        Retrieve unique device identifier (UDI) of the device:

        Reserved           4 bits
        Vendor             1 byte
        Product ID         6 bits
        Product revision   6 bits
        Serial number      2 bytes

        Total              4 bytes (32 bits)

        """
        response = proto.send_command(
            self.conn, proto.cmdGetUDI, proto.ENDPOINT_FW, 2)

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
        """
        Retrieve unique device identifier (UDI) as a hexadecimal string

        """
        reserved, vendor, pid, revision, serial = self.get_udi()
        return "{0:01x}:{1:04x}:{2:x}:{3:x}:{4:08x}".format(
            reserved, vendor, pid, revision, serial)


    def load_app(self, file, secret=None) -> None:
        """
        Load an application onto the device

        """
        # Calculate size and BLAKE2s digest from source file
        try:
            file_size = os.path.getsize(file)
            file_digest = self.get_digest(file)
        except FileNotFoundError as e:
            raise error.TKeyLoadError(e)

        # Ensure file size is not bigger than max allowed
        if file_size > APP_MAXSIZE:
            raise error.TKeyLoadError('File too big (%d > %d)' % \
                (file_size, APP_MAXSIZE))

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
        if secret != None:
            data[4] = 1
            data[5:7+len(secret)] = bytes(secret, encoding='utf8')

        response = proto.send_command(
            self.conn, proto.cmdLoadApp, proto.ENDPOINT_FW, 2, data)

        load_status = response[2]
        if load_status == 1:
            raise error.TKeyLoadError('Device not ready (1 = STATUS_BAD)')

        # Upload application data to device and get BLAKE2s digest
        result_digest = self.load_app_data(file_size, file)

        # Compare application hashes
        if not file_digest == result_digest:
            raise error.TKeyLoadError('Hash digests do not match (%s != %s)' % \
                                      (file_digest.hex(), result_digest.hex()))


    def load_app_data(self, file_size: int, file: str) -> bytes:
        """
        Load application data onto the device and return BLAKE2s digest

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
                self.conn, proto.cmdLoadAppData, proto.ENDPOINT_FW, 2, df)

            response_id, status = response[1:3]
            if status == 1:
                raise error.TKeyLoadError('Bad status when writing (1 = STATUS_BAD)')

            if response_id == proto.rspLoadAppDataReady.id:
                digest = bytes(response[3:][:32])
            elif not response_id == proto.rspLoadAppData.id:
                raise error.TKeyProtocolError('Unexpected response code (%d)' % response_id)

        return digest


    def get_digest(self, file) -> bytes:
        """
        Return BLAKE2s digest for given file as bytes

        """
        with open(file, 'rb') as f:
            data = f.read()
        return bytes.fromhex(blake2s(data, digest_size=32).hexdigest())
