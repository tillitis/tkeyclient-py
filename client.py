# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

import argparse
import sys

from datetime import datetime as dt

import cmd
import log


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Python client for interacting with the Tillitis TKey.',
        epilog='Copyright (c) %d Tillitis AB - https://tillitis.se' % dt.now().year)

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')

    subparsers = parser.add_subparsers(metavar='[command]')

    parser_dev = argparse.ArgumentParser(add_help=False)
    parser_dev.add_argument('device', type=str)
    parser_dev.add_argument('-s', '--speed', type=int, dest='speed', help='Baud rate')
    parser_dev.add_argument('-t', '--timeout', type=int, dest='timeout', help='Timeout (in seconds)')

    cmd_test = subparsers.add_parser('test', help='Check if given serial port can be opened', parents=[parser_dev])
    cmd_test.set_defaults(func=cmd.test_connection)

    cmd_load = subparsers.add_parser('load', help='Load application onto device', parents=[parser_dev])
    cmd_load.add_argument('-u', '--uss', action='store_true', dest='secret', help='Provide a user-supplied secret (USS)')
    cmd_load.add_argument('file', type=str)
    cmd_load.set_defaults(func=cmd.load_app)

    cmd_version = subparsers.add_parser('version', help='Get the name and version of stick', parents=[parser_dev])
    cmd_version.set_defaults(func=cmd.get_name_version)

    cmd_udi = subparsers.add_parser('udi', help='Get the unique device identifier (UDI)', parents=[parser_dev])
    cmd_udi.set_defaults(func=cmd.get_udi)

    args = parser.parse_args()

    logger = log.create_logger('root', 'DEBUG' if args.verbose else 'INFO')

    logger.debug('Initialized')

    if 'func' not in dir(args):
        logger.error('No command specified, exiting')
        sys.exit(1)

    result = args.func(args)

    if result is False:
        logger.debug('Exit status 1')
        sys.exit(1)

    logger.debug('Exit status 0')
