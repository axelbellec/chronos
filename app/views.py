# coding: utf-8

""" Chronos webapp views. """

from collections import OrderedDict

import datetime as dt
from flask import render_template

from app import app
from chronos.util import read_json, read_yaml
from chronos.config import CHRONOS_RUN_TIME

UPDATES = app.config['UPDATES']
CHRONOS_CONFIG = app.config['CHRONOS_CONFIG']

def get_updates():
    updates_by_school_year = read_json(UPDATES)
    for school_year, updates_times in updates_by_school_year.items():
        updates_by_school_year[school_year] = updates_times[-1]
    return OrderedDict(sorted(updates_by_school_year.items()))

def get_config():
    config = read_yaml(CHRONOS_CONFIG) 
    return OrderedDict(sorted(config.items()))

def humanize_date(date_str):
    """ Humanize a date. 
        After 24 hours just show the month and day. 
        After a year they start showing the last two 
        digits of the year.
    """
    date = dt.datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")    
    diff = dt.datetime.utcnow() - date

    if diff.days > 7 or diff.days < 0:
        return date.strftime('%d %b %y')
    elif diff.days == 1:
        return 'il y a 1 jour'
    elif diff.days > 1:
        return 'il y a {} jours'.format(round(diff.days))
    elif diff.seconds <= 1:
        return "à l'instant"
    elif diff.seconds < 60:
        return 'il y a quelques secondes {}'.format(round(diff.seconds))
    elif diff.seconds < 120:
        return 'il y a 1 minute'
    elif diff.seconds < 3600:
        return 'il y a {} minutes'.format(round(diff.seconds/60))
    elif diff.seconds < 7200:
        return 'il y a 1 heure'
    else:
        return 'il y a {} heures'.format(round(diff.seconds/3600))

@app.route('/', methods=['GET'])
def main_route():
    chronos_updates = get_updates()
    chronos_config = get_config()
    for school_year in chronos_config.keys():
        chronos_config[school_year]['update_time'] = chronos_updates[school_year]
    
    with open(CHRONOS_RUN_TIME, 'r') as f:
        last_run = f.read()

    app.logger.info('getting updates: %s', chronos_updates)
    return render_template('index.html', title='Chronos', data=chronos_config, 
                            humanize_date=humanize_date, 
                            last_update_time=last_run)
