# Copyright (C) 2022-2025 - Tillitis AB
# SPDX-License-Identifier: BSD-2-Clause

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
