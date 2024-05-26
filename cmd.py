import logging

from tkeyclient.error import TKeyError
from tkeyclient.tkey import TKey


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
