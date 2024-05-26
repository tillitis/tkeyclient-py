import serial

import tkeyclient.error as error


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
