# coding: utf-8

import os
import redis

from flask import Flask


# Init App
NAMESPACE = 'app'
app = Flask(NAMESPACE)

# Configure the application
app.config.from_object('app.config')

# Building a cache instance
redis_conf = dict(decode_responses=True)
if not app.config.get('REDIS_URL'):
    cache = redis.Redis(**redis_conf)
else:
    cache = redis.from_url(app.config.get('REDIS_URL'), **redis_conf)

# Set a custom secret key
app.secret_key = 'chronos'

from app import views
