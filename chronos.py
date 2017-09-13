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
from apiclient.http import BatchHttpRequest
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
NB_RESULTS = 250


def getData(force_update):
    """
    Download XML file and parse it.
    """

    # Download schedule
    download_file(URL, XML_FILE)

    # Read XML data
    xml_data = read_xml(XML_FILE)

    # Give it to Beautiful Soup for pretty parsing
    soup = BeautifulSoup(xml_data, 'html.parser')

    update_time_regex = re.compile(r'\d{2}\/\d{2}\/\d{4}\s?\d{2}:\d{2}:\d{2}')
    update_time = update_time_regex.findall(soup.find('footer').get_text())[0]

    # If there is no backup file containing updates
    if not os.path.isfile(UPDATES_BACKUP):
        updates = dict(update_time=[update_time])
    else:
        updates = read_json(file=UPDATES_BACKUP)

        if update_time in updates['update_time']:
            print('Schedule has not been updated yet')
            if not force_update:
                return

        updates['update_time'].append(update_time)
        updates['update_time'] = list(set(updates['update_time']))

    write_json(file=UPDATES_BACKUP, data=json.dumps(updates))

    # Compute a correspondance tables between 'rawweeks' and the first weekday
    dates = {
        span.alleventweeks.get_text(): span['date'] for span in soup.find_all('span')
    }

    document = soup.find_all('event')

    events = extract_events_info(document, dates)

    click.secho('CELCAT events formatted ({})'.format(len(events)), fg='cyan')
    return events


def extract_events_info(document, dates):
    """
    Parse and extract data from XML balises.

    Args :
        -document : bs4 parsed document
        -dates : dict mapping
    Return :
        list of all formatted events
    """

    events = []
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
            dtstart = datetime.datetime.strptime(
                start, '%d/%m/%Y-%H:%M') + datetime.timedelta(days=nday, hours=-2)
            dtend = datetime.datetime.strptime(
                end, '%d/%m/%Y-%H:%M') + datetime.timedelta(days=nday, hours=-2)

            start_date = dtstart.isoformat() + 'Z'
            end_date = dtend.isoformat() + 'Z'

            calendar_event = Google_Calendar_Event(
                location=room,
                summary='({}) - {} - {}'.format(category, name, group),
                description=group,
                dtstart=start_date,
                dtend=end_date)

            events.append(calendar_event.bloc())
    return events


def delete_events(service, min_date):
    """
    Delete all events on a Google Calendar ID
    """

    # Get all events
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    eventsResult = service.events().list(
        calendarId=CALENDAR_ID, timeMin=min_date, maxResults=NB_RESULTS, singleEvents=True,
        orderBy='startTime').execute()

    events = eventsResult.get('items', [])
    click.secho('Google Agenda events found ({})'.format(len(events)), fg='cyan')

    batch = service.new_batch_http_request()
    if events:
        click.secho('Deleting events on Google Agenda ({})'.format(len(events)), fg='cyan')
        with click.progressbar(events, label='Deleting events', length=len(events)) as bar:
            # Delete all events
            for event in bar:
                try:
                    batch.add(service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']))
                except HttpError as err:
                    raise err
            batch.execute()


def insert_events(service, data):
    """
    Insert all events on a Google Calendar ID
    """

    batch = service.new_batch_http_request()
    click.secho('Inserting events on Google Agenda ({})'.format(len(data)), fg='cyan')
    with click.progressbar(data, label='Updating events', length=len(data)) as bar:
        # Insert events
        for new_event in bar:
            try:
                batch.add(service.events().insert(calendarId=CALENDAR_ID,
                                                  body=new_event, sendNotifications=True))
            except HttpError as err:
                raise err
        batch.execute()


def authorize_api():
    """
    Compute Google authentification process
    """

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

    return build('calendar', 'v3', http=http)


def find_min_date(data):
    """ Find the lowest date in a set """
    dt = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
    dates = [dt(event['start']['dateTime'][:-2]) for event in data]
    return min(dates).isoformat() + 'Z'


@click.command()
@click.option('--force/--no-force', help='Force schedule update', default=False)
@click.option('--delete/--no-delete', help='Delete all old events', default=True)
@click.option('--insert/--no-insert', help='Insert all new events', default=True)
@click.option('--alert/--no-alert', help='Push alert to Slack channel', default=False)
def main(force, delete, insert, alert):
    data = getData(force)

    if data:

        try:
            service = authorize_api()

            if delete:
                min_date = find_min_date(data)
                delete_events(service, min_date)
            if insert:
                insert_events(service, data)
            if alert:
                if not SLACK_URL:
                    click.secho('Slack webhook URL is undefined.', fg='red')
                else:
                    slack = Slacker(webhook=SLACK_URL)
                    slack.send(
                        msg="L'emploi du temps a été mis à jour.",
                        channel='#emploidutemps'
                    )
                    click.secho('Notification pushed to Slack', fg='cyan')

        except AccessTokenRefreshError:
            # The AccessTokenRefreshError exception is raised if the credentials
            # have been revoked by the user or they have expired.
            print('The credentials have been revoked or expired, please re-run'
                  'the application to re-authorize')


if __name__ == '__main__':
    main()
