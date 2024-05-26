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
    logger.info('Attempting to open serial port: %s' % args.device)
    with TKey(args.device, connect=True) as tk:
        try:
            if tk.test() is True:
                logger.info('Serial port is open!')
        except TKeyError as e:
            logger.error('Connection failed: %s' % e)
            return False


def get_name_version(args):
    """
    Retrieve the name and version of the given device

    """
    with TKey(args.device, connect=True) as tk:
        try:
            name0, name1, version = tk.get_name_version()
            logger.info('Firmware name0:%s name1:%s version:%d' % \
                (name0, name1, version))
        except TKeyError as e:
            logger.error('Failed to get device info: %s' % e)


def get_udi(args):
    """
    Retrieve unique device identifier (UDI) of the given device

    """
    with TKey(args.device, connect=True) as tk:
        try:
            logger.info("Got UDI: %s" % tk.get_udi_string())
        except TKeyError as e:
            logger.error('Failed to get UDI: %s' % e)


def load_app(args):
    """
    Load an application onto the given device

    """
    # Prompt for user-supplied secret if requested
    secret = None
    if args.secret == True:
        logger.debug('Asking for user-supplied secret (USS)')
        secret = getpass.getpass(prompt='Enter secret: ')

    with TKey(args.device, connect=True) as tk:
        try:
            tk.load_app(args.file, secret)
            logger.info('Application loaded: %s' % args.file)
        except TKeyError as e:
            logger.error('Failed to load application on device: %s' % e)
