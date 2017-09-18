# coding: utf-8

import os

HOST = 'localhost'
PORT = 5000

UPDATES = os.path.join('data', 'updates.json')
CHRONOS_CONFIG = 'config.yml'

REDIS_URL = os.environ.get('REDISCLOUD_URL')
