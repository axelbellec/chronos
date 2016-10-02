import os
import httplib2
import sys
import json
import re

import click
import dotenv
import lxml
import datetime

from bs4 import BeautifulSoup
from apiclient.errors import HttpError
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow


from util import download_file, read_xml, read_json, write_json
from util import Google_Calendar_Event, Slacker

dotenv.load()

URL = os.environ.get('SCHEDULE_URL')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
CALENDAR_ID = os.environ.get('CALENDAR_ID')
SLACK_URL = os.environ.get('SLACK_URL')

XML_FILE = 'edt.xml'
UPDATES_BACKUP = 'updates.json'
SCOPE = ['https://www.googleapis.com/auth/calendar']
NB_RESULTS = 200


def getData(force_update):
    # Download schedule
    # download_file(URL, XML_FILE)

    # Read XML data
    xml_data = read_xml(XML_FILE)

    # Give it to Beautiful Soup for pretty parsing
    soup = BeautifulSoup(xml_data, "html.parser")

    update_time_regex = re.compile(r'\d{2}\/\d{2}\/\d{4}\s?\d{2}:\d{2}:\d{2}')
    update_time = update_time_regex.findall(soup.find('footer').get_text())[0]

    updates = read_json(file=UPDATES_BACKUP)

    if update_time in updates['update_time']:
        print('Schedule has not been updated yet')
        if not force_update:
            return

    updates['update_time'].append(update_time)
    updates['update_time'] = list(set(updates['update_time']))

    write_json(file=UPDATES_BACKUP, data=json.dumps(updates))

    # Compute a correspondance tables between 'rawweeks' and the first weekday
    dates = {span.alleventweeks.get_text(): span['date'] for span in soup.find_all('span')}

    events = []

    document = soup.find_all('event')
    click.secho('Formatting CELCAT events ({})'.format(len(document)), fg='cyan')
    with click.progressbar(document, label='Formatting events', length=len(document)) as bar:
        for event in bar:
            name = event.module.get_text().replace('\n', '') if event.module else 'Matière non définie'
            category = event.category.get_text() if event.category else 'Catégorie de cours non définie'
            starttime = event.starttime.get_text() if event.starttime else 'Heure de début de cours non définie'
            endtime = event.endtime.get_text() if event.endtime else 'Heure de début de cours non définie'
            room = event.room.item.get_text() if event.room and event.room.item else 'Aucune salle définie'
            group = event.group.item.get_text() if event.group and event.group.item else 'Classe entière'
            nday = int(event.day.get_text()) if event.day else None
            date_first_weekday = dates[event.rawweeks.get_text()] if event.rawweeks else None
            start = '{}-{}'.format(date_first_weekday, starttime)
            end = '{}-{}'.format(date_first_weekday, endtime)
            dtstart = datetime.datetime.strptime(start, '%d/%m/%Y-%H:%M') + datetime.timedelta(days=nday, hours=-2)
            dtend = datetime.datetime.strptime(end, '%d/%m/%Y-%H:%M') + datetime.timedelta(days=nday, hours=-2)

            start_date = dtstart.isoformat() + 'Z'
            end_date = dtend.isoformat() + 'Z'

            calendar_event = Google_Calendar_Event(
                location=room,
                summary='({}) - {} - {}'.format(category, name, group),
                description=group,
                dtstart=start_date,
                dtend=end_date)

            events.append(calendar_event.bloc())

    click.secho('CELCAT events formatted ({})'.format(len(events)), fg='cyan')
    return events


def delete_events(service):
    # Get all events
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    eventsResult = service.events().list(
        calendarId=CALENDAR_ID, timeMin=now, maxResults=NB_RESULTS, singleEvents=True,
        orderBy='startTime').execute()

    events = eventsResult.get('items', [])
    click.secho('Google Agenda events found ({})'.format(len(events)), fg='cyan')

    if events:
        click.secho('Deleting events on Google Agenda ({})'.format(len(events)), fg='cyan')
        with click.progressbar(events, label='Deleting events', length=len(events)) as bar:
            # Delete all events
            for event in bar:
                try:
                    deleted_event = service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
                except HttpError as err:
                    raise err


def insert_events(service, data):
    click.secho('Inserting events on Google Agenda ({})'.format(len(data)), fg='cyan')
    with click.progressbar(data, label='Updating events', length=len(data)) as bar:
            # Insert events
        for new_event in bar:
            try:
                service.events().insert(calendarId=CALENDAR_ID,
                                        body=new_event, sendNotifications=True).execute()
            except HttpError as err:
                raise err


@click.command()
@click.option('--force', help='Force schedule update', default=False)
def main(force):

    data = getData(force)

    if data:
        flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, SCOPE)
        storage = Storage('credentials.dat')
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, tools.argparser.parse_args())

        # Create an httplib2.Http object to handle our HTTP requests, and authorize it
        # using the credentials.authorize() function.
        http = httplib2.Http()
        http = credentials.authorize(http)
        # httplib2.debuglevel = 4

        service = build('calendar', 'v3', http=http)

        try:
            delete_events(service)

            insert_events(service, data)

            slack = Slacker(SLACK_URL)
            slack.send(
                msg="L'emploi du temps a été mis à jour.",
                channel='#emploidutemps'
            )

        except AccessTokenRefreshError:
            # The AccessTokenRefreshError exception is raised if the credentials
            # have been revoked by the user or they have expired.
            print('The credentials have been revoked or expired, please re-run'
                  'the application to re-authorize')


if __name__ == '__main__':
    main()
