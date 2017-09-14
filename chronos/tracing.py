# coding: utf-8

import os
import logging

from chronos.config import LOG_LEVEL

def log_factory(namespace=__name__, level=None):
    """ Opinionated logger factory. """

    level = level or LOG_LEVEL
    logging.basicConfig(level=level.upper())
    logger = logging.getLogger(namespace)
    return logger