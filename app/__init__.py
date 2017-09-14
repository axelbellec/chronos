# coding: utf-8

import os

from flask import Flask

# Init App
NAMESPACE = 'app'
app = Flask(NAMESPACE)

# Configure the application
app.config.from_object('app.config')

# Set a custom secret key
app.secret_key = 'chronos'

from app import views
