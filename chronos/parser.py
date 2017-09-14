# coding: utf-8

""" A simple .pdf parser that extracts school timetables and push them
into a Google Calendar. """

import os
import json
import re

import click
import datetime
import httplib2
import dotenv

from bs4 import BeautifulSoup
from apiclient.errors import HttpError
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow

from chronos.util import download_file, read_xml, read_json, write_json
from chronos.event import GoogleCalendarEvent

dotenv.load()

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

UPDATES_BACKUP = os.path.join('data', 'updates.json')
SCOPE = ['https://www.googleapis.com/auth/calendar']
NB_RESULTS = 300


class TimetableParser(object):
    """ A custom Parser to extract events from an XML file. """

    def __init__(self, school_year, schedule_url, description, google_calendar_id, force_update=False):
        self.school_year = school_year
        self.schedule_url = schedule_url
        self.description = description
        self.google_calendar_id = google_calendar_id
        self.force_update = force_update

        self.formatted_events = []
        self.schedule_is_new = True
        
        self.update_time = None
        self.week_dates_mapping = None
        self.unformatted_events = None
        self.min_date = None
        self.service = None

    @property
    def schedule_filename(self):
        return os.path.join('data', 'timetable_{}.xml'.format(self.school_year))

    def save_update_time(self):
        if not os.path.isfile(UPDATES_BACKUP):
            updates = {
                self.school_year: [self.update_time]
            }
        else:
            updates = read_json(file=UPDATES_BACKUP)

            if self.update_time in updates.get(self.school_year, []):
                print('Timetable for "{}" has not been updated yet.'.format(self.school_year))
                if not self.force_update:
                    self.schedule_is_new = False

            if not self.school_year in updates.keys():
                updates[self.school_year] = [self.update_time]
            else:
                updates[self.school_year].append(self.update_time)

            updates[self.school_year] = list(set(updates[self.school_year]))

        write_json(file=UPDATES_BACKUP, data=json.dumps(updates))

    def get_timetable(self):
        """ Download an XML file and parse it. """

        # Download schedule
        download_file(self.schedule_url, self.schedule_filename)

        # Read XML data
        xml_data = read_xml(self.schedule_filename)

        # Give it to Beautiful Soup for pretty parsing
        soup = BeautifulSoup(xml_data, 'html.parser')

        update_time_regex = re.compile(r'\d{2}\/\d{2}\/\d{4}\s?\d{2}:\d{2}:\d{2}')
        self.update_time = update_time_regex.findall(soup.find('footer').get_text())[0]

        self.save_update_time()

        # Compute a correspondance tables between 'rawweeks' and the first weekday
        self.week_dates_mapping = {
            span.alleventweeks.get_text(): span['date'] 
            for span in soup.find_all('span')
        }

        self.unformatted_events = soup.find_all('event')

    def find_min_date(self):
        """ Find the lowest date in a set. """

        to_datetime = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
        all_dates = [to_datetime(event['start']['dateTime'][:-2]) for event in self.formatted_events]
        self.min_date = min(all_dates).isoformat() + 'Z'

    def format_events(self):
        """ Parse and format events from XML data. """

        click.secho('Formatting CELCAT events ({})'.format(len(self.unformatted_events)), fg='cyan')
        with click.progressbar(self.unformatted_events, label='Formatting events', length=len(self.unformatted_events)) as events:
            for event in events:
                name = event.module.get_text().replace('\n', '') if event.module else 'Matière non définie'
                category = event.category.get_text() if event.category else 'Catégorie de cours non définie'
                starttime = event.starttime.get_text() if event.starttime else 'Heure de début de cours non définie'
                endtime = event.endtime.get_text() if event.endtime else 'Heure de début de cours non définie'
                room = event.room.item.get_text() if event.room and event.room.item else 'Aucune salle définie'
                group = event.group.item.get_text() if event.group and event.group.item else 'Classe entière'
                nday = int(event.day.get_text()) if event.day else None
                date_first_weekday = self.week_dates_mapping[event.rawweeks.get_text()] if event.rawweeks else None
                start = '{}-{}'.format(date_first_weekday, starttime)
                end = '{}-{}'.format(date_first_weekday, endtime)
                dtstart = datetime.datetime.strptime(start, '%d/%m/%Y-%H:%M') + datetime.timedelta(days=nday, hours=-2)
                dtend = datetime.datetime.strptime(end, '%d/%m/%Y-%H:%M') + datetime.timedelta(days=nday, hours=-2)

                start_date = dtstart.isoformat() + 'Z'
                end_date = dtend.isoformat() + 'Z'

                calendar_event = GoogleCalendarEvent(
                    location=room,
                    summary='({}) - {} - {}'.format(category, name, group),
                    description=group,
                    dtstart=start_date,
                    dtend=end_date
                )
                self.formatted_events.append(calendar_event.json)

    def authorize_api(self):
        """ Compute Google authentification process. """

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

    def process(self):
        """ Download the timetable XML file, parse it and format events if
            the schedule is new.
        """
        self.get_timetable()

        if self.schedule_is_new:
            self.format_events()
            self.find_min_date()
            click.secho('CELCAT events formatted ({})'.format(len(self.formatted_events)), fg='cyan')

            self.service = self.authorize_api()
            try:
                self.delete_events()
                self.insert_events()
            except AccessTokenRefreshError:
                # The AccessTokenRefreshError exception is raised if the credentials
                # have been revoked by the user or they have expired.
                print('The credentials have been revoked or expired, please re-run'
                    'the application to re-authorize')

    def delete_events(self):
        """ Delete all events on a Google Calendar ID. """

        # Get all events
        events_result = self.service.events().list(
            calendarId=self.google_calendar_id, timeMin=self.min_date, maxResults=NB_RESULTS, singleEvents=True,
            orderBy='startTime').execute()

        events = events_result.get('items', [])
        click.secho('Google Agenda events found ({})'.format(len(events)), fg='cyan')

        batch = self.service.new_batch_http_request()
        if events:
            click.secho('Deleting events on Google Agenda ({})'.format(len(events)), fg='cyan')
            with click.progressbar(events, label='Deleting events', length=len(events)) as bar:
                # Delete all events
                for event in bar:
                    try:
                        batch.add(self.service.events().delete(calendarId=self.google_calendar_id, eventId=event['id']))
                    except HttpError as err:
                        raise err
                batch.execute()


    def insert_events(self):
        """ Insert all events on a Google Calendar ID. """

        batch = self.service.new_batch_http_request()
        click.secho('Inserting events on Google Agenda ({})'.format(len(self.formatted_events)), fg='cyan')
        with click.progressbar(self.formatted_events, label='Updating events', length=len(self.formatted_events)) as events:
            # Insert events
            for event in events:
                try:
                    batch.add(self.service.events().insert(calendarId=self.google_calendar_id,
                                                    body=event, sendNotifications=True))
                except HttpError as err:
                    raise err
            batch.execute()

