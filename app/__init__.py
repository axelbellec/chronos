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
cache = redis.from_url(app.config.get('REDIS_URL'))

# Set a custom secret key
app.secret_key = 'chronos'

from app import views
