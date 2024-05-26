# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

import getpass
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

    # Prompt for user-supplied secret if requested
    secret = None
    if args.secret == True:
        logger.debug('Asking for user-supplied secret (USS)')
        secret = getpass.getpass(prompt='Enter secret: ')

    try:
        tk.connect()
        tk.load_app(args.file, secret)
        logger.info('Application loaded: %s' % args.file)
    except TKeyError as e:
        logger.error('Failed to load application on device: %s' % e)
    finally:
        tk.disconnect()
