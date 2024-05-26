import argparse

from datetime import datetime as dt

import log


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Python client for interacting with the Tillitis TKey.',
        epilog='Copyright (c) %d Tillitis AB - https://tillitis.se' % dt.now().year)

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')

    args = parser.parse_args()

    logger = log.create_logger('root', 'DEBUG' if args.verbose else 'INFO')

    logger.debug('Initialized')
