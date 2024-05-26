import serial

import tkeyclient.error as error
import tkeyclient.proto as proto


# Defaults for serial communication with the TKey
DEFAULT_SPEED = 62500
DEFAULT_TIMEOUT = 1


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


    def connect(self):
        """
        Open connection to the given serial device

        """
        try:
            self.conn.open()
        except serial.SerialException as e:
            raise error.TKeyConnectionError(e)


    def disconnect(self):
        """
        Close connection to the serial device

        """
        self.conn.close()


    def test(self):
        """
        Test if serial connection is open

        """
        return self.conn.is_open


    def get_name_version(self):
        """
        Retrieve name and version of the device

        """
        endpoint = proto.ENDPOINT_FW
        cmd_id   = proto.FW_CMD_NAME_VERSION
        length   = 0
        frame_id = 2

        frame = proto.create_frame(cmd_id, frame_id, endpoint, length)

        self.connect()

        try:
            proto.write_frame(self.conn, frame)
        except serial.SerialException as e:
            raise error.TKeyWriteError(e)

        try:
            response = proto.read_frame(self.conn)
        except serial.SerialException as e:
            raise error.TKeyReadError(e)

        data = response[2:]

        name0 = data[0:][:4].decode('ascii').rstrip()
        name1 = data[4:][:4].decode('ascii').rstrip()

        version = int.from_bytes(data[8:][:4], byteorder='little')

        return name0, name1, version
