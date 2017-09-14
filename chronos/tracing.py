# coding: utf-8

import os
import logging

def log_factory(namespace=__name__, level=None):
    """ Opinionated logger factory. """

    level = level or os.environ.get('LOG_LEVEL', 'info')
    logging.basicConfig(level=level.upper())
    logger = logging.getLogger(namespace)
    return logger