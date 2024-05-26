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

    def __init__(self, device, speed=DEFAULT_SPEED, timeout=DEFAULT_TIMEOUT):
        """
        Create new instance of a TKey object

        """
        self.conn = serial.Serial()

        self.conn.port = device
        self.conn.baudrate = speed
        self.conn.timeout = timeout


    def connect(self) -> None:
        """
        Open connection to the given serial device

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
        cmd      = proto.cmdNameVersion
        endpoint = proto.ENDPOINT_FW
        frame_id = 2

        frame = proto.create_frame(cmd, frame_id, endpoint)

        proto.write_frame(self.conn, frame)

        response = proto.read_frame(self.conn)

        if not proto.ensure_frames(frame, response):
            raise error.TKeyProtocolError('Response mismatch')

        data = response[2:]

        name0 = data[0:][:4].decode('ascii').rstrip()
        name1 = data[4:][:4].decode('ascii').rstrip()

        version = int.from_bytes(data[8:][:4], byteorder='little')

        return name0, name1, version


    def load_app(self, file, secret=None) -> None:
        """
        Load an application onto the device

        """
        cmd      = proto.cmdLoadApp
        endpoint = proto.ENDPOINT_FW
        frame_id = 2

        # Create header and command bytes
        frame = proto.create_frame(cmd, frame_id, endpoint)

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

        # Set size for application payload (4 bytes, little endian)
        size_bytes = int(file_size).to_bytes(4, byteorder='little')
        frame[2] = size_bytes[0]
        frame[3] = size_bytes[1]
        frame[4] = size_bytes[2]
        frame[5] = size_bytes[3]

        # Handle user-supplied secret if provided
        frame[6] = 0
        if secret != None:
            frame[6] = 1
            frame[7:7+len(secret)] = bytes(secret, encoding='utf8')

        proto.write_frame(self.conn, frame)

        response = proto.read_frame(self.conn)

        if not proto.ensure_frames(frame, response):
            raise error.TKeyProtocolError('Response mismatch')

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
        cmd      = proto.cmdLoadAppData
        endpoint = proto.ENDPOINT_FW
        frame_id = 2

        # Create header and command bytes
        frame = proto.create_frame(cmd, frame_id, endpoint)

        dataframes = []

        with io.open(file, 'rb') as f:
            bytes_read = 0
            while bytes_read < file_size:
                data = f.read(127)
                dataframes.append(data)
                bytes_read += len(data)

        digest = bytearray(32)

        for df in dataframes:

            # Create a full frame with header, command and data
            appframe = bytearray(frame)
            appframe[2:2+len(df)] = df

            proto.write_frame(self.conn, appframe)

            response = proto.read_frame(self.conn)

            if not proto.ensure_frames(appframe, response):
                raise error.TKeyProtocolError('Response mismatch')

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
