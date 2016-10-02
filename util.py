import json

import requests
import datetime as dt
from tqdm import tqdm


def download_file(url, output):
    response = requests.get(url, stream=True)

    assert response.status_code == 200

    with open(output, 'wb') as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)


def read_xml(file):
    with open(file, 'r') as f:
        content = f.read()
    return content


def read_json(file):
    with open(file, 'r') as json_data:
        return json.load(json_data)


def write_json(file, data):
    with open(file, 'w') as json_data:
        json_data.write(data)


def datetime_to_ics(date):
    return '{year}{month}{day}T{hour}{min}00'.format(
        year=date.year,
        month='0' + str(date.month) if date.month < 10 else date.month,
        day='0' + str(date.day) if date.day < 10 else date.day,
        hour='0' + str(date.hour) if date.hour < 10 else date.hour,
        min='0' + str(date.minute) if date.minute < 10 else date.minute
    )


class ICS_Event():

    def __init__(self, location=None, summary=None, description=None, dtstart=None, dtend=None):
        self.begin = 'BEGIN:VEVENT'
        self.location = 'LOCATION:{}'.format(location)
        self.summary = 'SUMMARY:{}'.format(summary)
        self.description = 'DESCRIPTION:{}'.format(description)
        self.dtstart = 'DTSTART:{}'.format(dtstart)
        self.dtend = 'DTEND:{}'.format(dtend)
        self.end = 'END:VEVENT'

    def bloc(self):
        return '\n'.join([self.begin, self.location, self.summary, self.description, self.dtstart, self.dtend, self.end])


class Google_Calendar_Event():

    def __init__(self, location=None, summary=None, description=None, dtstart=None, dtend=None):
        self.json = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': dtstart,
                'timeZone': 'Europe/Paris',
            },
            'end': {
                'dateTime': dtend,
                'timeZone': 'Europe/Paris',
            },
            'recurrence': [],
            'attendees': [],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
            'creator': {
                'displayName': 'Axel Bellec',
                'email': 'abellec.22@gmail.com'
            }
        }

    def bloc(self):
        return self.json


class Slacker():

    def __init__(self, webhook=None):
        self.webhook_url = webhook

    def send(self, msg=None, channel=None):
        payload = {
            "text": msg,
            "channel": channel
        }
        requests.post(self.webhook_url, json=payload)
