import os
import json

import dotenv

dotenv.load()

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

CHRONOS_FORCE_UPDATE = json.loads(os.environ.get('FORCE_UPDATE')) or False

UPDATES_BACKUP = os.path.join('data', 'updates.json')
SCOPE = ['https://www.googleapis.com/auth/calendar']
NB_RESULTS = 300

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info')