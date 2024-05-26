# Copyright (C) 2022-2024 - Tillitis AB
# SPDX-License-Identifier: GPL-2.0-only

import logging


def create_logger(name, level='INFO'):
    formatter = logging.Formatter(
        fmt='%(asctime)s - [%(levelname)s] %(module)s: %(message)s'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(fmt=formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
