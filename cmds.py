# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

import getpass
import logging

from tkeyclient.hw import find_device
from tkeyclient.error import TKeyError
from tkeyclient.tkey import TKey


logger = logging.getLogger('root')


def create_handler(func):
    """
    Create wrapper for a client subcommand handler

    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TKeyError as e:
            logger.error('[{0}] {1}: {2}'.format(func.__name__, type(e).__name__, e))
            return False

    return wrapper


def test_connection(args):
    """
    Check if serial connection can be opened to the given device

    """
    port = get_device(args)
    logger.info('Attempting to open serial port: %s' % port)
    with TKey(port, connect=True) as tk:
        if tk.test() is True:
            logger.info('Serial port is open!')


def get_name_version(args):
    """
    Retrieve the name and version of the given device

    """
    with TKey(get_device(args), connect=True) as tk:
        name0, name1, version = tk.get_name_version()
        logger.info('Firmware name0:%s name1:%s version:%d' % (name0, name1, version))


def get_udi(args):
    """
    Retrieve unique device identifier (UDI) of the given device

    """
    with TKey(get_device(args), connect=True) as tk:
        logger.info('Got UDI: %s' % tk.get_udi_string())


def load_app(args):
    """
    Load an application onto the given device

    """
    # Prompt for user-supplied secret if requested
    secret = None
    if args.secret:
        logger.debug('Asking for user-supplied secret (USS)')
        secret = getpass.getpass(prompt='Enter secret: ')

    with TKey(get_device(args), connect=True) as tk:
        tk.load_app(args.file, secret)
        logger.info('Application loaded: %s' % args.file)


def get_device(args):
    """
    Return device path to use (automatically or manually)

    """
    if args.auto:
        logger.debug('Scanning for connected TKey devices...')
        d = find_device()
        logger.debug('Found device: %s (%s %s)' % (d.device, d.manufacturer, d.product))
        return d.device

    return args.device
