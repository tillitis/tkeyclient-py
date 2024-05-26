import logging

from tkeyclient.error import TKeyError
from tkeyclient.tkey import TKey

import tkeyclient.proto as proto


logger = logging.getLogger('root')


def test_connection(args):
    """
    Check if serial connection can be opened to the given device

    """
    tk = TKey(args.device)

    try:
        logger.info('Attempting to open serial port: %s' % args.device)
        tk.connect()
        if tk.test() is True:
            logger.info('Serial port is open!')
        tk.disconnect()
    except TKeyError as e:
        logger.error('Connection failed: %s' % e)
        return False


def get_name_version(args):
    """
    Retrieve the name and version of the given device

    """
    tk = TKey(args.device)

    try:
        name0, name1, version = tk.get_name_version()
        logger.info('Firmware name0:%s name1:%s version:%d' % \
            (name0, name1, version))
    except TKeyError as e:
        logger.error('Failed to get device info: %s' % e)
