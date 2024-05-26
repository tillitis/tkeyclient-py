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
    except TKeyError as e:
        logger.error('Connection failed: %s' % e)
        return False
    finally:
        tk.disconnect()


def get_name_version(args):
    """
    Retrieve the name and version of the given device

    """
    tk = TKey(args.device)

    try:
        tk.connect()
        name0, name1, version = tk.get_name_version()
        logger.info('Firmware name0:%s name1:%s version:%d' % \
            (name0, name1, version))
    except TKeyError as e:
        logger.error('Failed to get device info: %s' % e)
    finally:
        tk.disconnect()


def load_app(args):
    """
    Load an application onto the given device

    """
    tk = TKey(args.device)

    try:
        tk.connect()
        tk.load_app(args.file)
        logger.info('Application loaded: %s' % args.file)
    except TKeyError as e:
        logger.error('Failed to load application on device: %s' % e)
    finally:
        tk.disconnect()
