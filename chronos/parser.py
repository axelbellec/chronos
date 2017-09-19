# coding: utf-8

""" A simple .pdf parser that extracts school timetables and push them
into a Google Calendar. """

import os
import json
import re

import click
import datetime
import httplib2

from bs4 import BeautifulSoup
from apiclient.errors import HttpError
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow

from chronos.util import download_file, read_file, read_json, write_json
from chronos.event import GoogleCalendarEvent
from chronos.tracing import log_factory
from chronos.config import CLIENT_ID, CLIENT_SECRET, SCOPE, NB_RESULTS, LOG_LEVEL
from app import cache

log = log_factory(__name__, LOG_LEVEL)

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
        log.debug('trying to save update time for "{}"'.format(self.school_year))
        
        # Get all updates for the school_year
        updates = cache.lrange(self.school_year, 0, -1)

        if self.update_time in updates:
            if not self.force_update:
                self.schedule_is_new = False

        # Insert update time into broker
        cache.rpush(self.school_year, self.update_time)

        # Insert chronos runtime into broker
        now = datetime.datetime.now() + datetime.timedelta(hours=2)
        chronos_last_run = str(datetime.datetime.strftime(now, '%d/%m/%Y %H:%M:%S'))            
        cache.set('chronos_last_run', chronos_last_run)


    def get_timetable(self):
        """ Download an XML file and parse it. """

        # Download schedule
        log.debug('downloading timetable for "{}"'.format(self.school_year))
        download_file(self.schedule_url, self.schedule_filename)

        # Read XML data
        xml_data = read_file(self.schedule_filename)

        # Give it to Beautiful Soup for pretty parsing
        soup = BeautifulSoup(xml_data, 'html.parser')

        update_time_regex = re.compile(r'\d{2}\/\d{2}\/\d{4}\s?\d{2}:\d{2}:\d{2}')
        update_time_str = update_time_regex.findall(soup.find('footer').get_text())[0]
        update_time_dt = datetime.datetime.strptime(update_time_str, '%d/%m/%Y %H:%M:%S')
        self.update_time = str(datetime.datetime.strftime(update_time_dt, '%d/%m/%Y %H:%M:%S'))            

        self.save_update_time()

        # Compute a correspondance tables between 'rawweeks' and the first weekday
        self.week_dates_mapping = {
            span.alleventweeks.get_text(): span['date'] 
            for span in soup.find_all('span')
        }

        log.debug('find all events for "{}".'.format(self.school_year))
        self.unformatted_events = soup.find_all('event')

    def find_min_date(self):
        """ Find the lowest date in a set. """

        to_datetime = lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")
        all_dates = [to_datetime(event['start']['dateTime'][:-2]) for event in self.formatted_events]
        self.min_date = min(all_dates).isoformat() + 'Z'

    def format_events(self):
        """ Parse and format events from XML data. """

        log.debug('formatting events ({}) for "{}"'.format(len(self.unformatted_events), self.school_year))
        for event in self.unformatted_events:
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

        log.debug('computing Google authentification process for "{}"'.format(self.school_year))
        flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, SCOPE)
        storage = Storage('credentials.dat')
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, tools.argparser.parse_args())

        # Create an httplib2.Http object to handle our HTTP requests, and authorize it
        # using the credentials.authorize() function.
        http = httplib2.Http()
        http = credentials.authorize(http)
        httplib2.debuglevel = 0

        return build('calendar', 'v3', http=http)

    def process(self):
        """ Download the timetable XML file, parse it and format events if
            the schedule is new.
        """
        self.get_timetable()

        if self.schedule_is_new:
            log.debug('timetable for "{}" has been updated'.format(self.school_year))
            self.format_events()
            self.find_min_date()
            log.debug('events formatted ({}) for "{}"'.format(len(self.formatted_events), self.school_year))

            self.service = self.authorize_api()
            try:
                self.delete_events()
                self.insert_events()
            except AccessTokenRefreshError:
                # The AccessTokenRefreshError exception is raised if the credentials
                # have been revoked by the user or they have expired.
                print('The credentials have been revoked or expired, please re-run'
                    'the application to re-authorize')
        else:
            log.debug('timetable for "{}" has not been updated yet'.format(self.school_year))

    def delete_events(self):
        """ Delete all events on a Google Calendar ID. """

        # Get all events
        events_result = self.service.events().list(
            calendarId=self.google_calendar_id, timeMin=self.min_date, maxResults=NB_RESULTS, singleEvents=True,
            orderBy='startTime').execute()

        events = events_result.get('items', [])
        log.debug('{} Google Agenda events found for "{}"'.format(len(events), self.school_year))

        batch = self.service.new_batch_http_request()
        if events:
            log.debug('deleting {} events on Google Agenda for "{}"'.format(len(events), self.school_year))
            with click.progressbar(events, label='Deleting events', length=len(events)) as bar:
                # Delete all events
                for event in bar:
                    try:
                        delete_step = self.service.events().delete(
                            calendarId=self.google_calendar_id, 
                            eventId=event['id']
                        )
                        batch.add(delete_step)
                    except HttpError as err:
                        raise err
                batch.execute()


    def insert_events(self):
        """ Insert all events on a Google Calendar ID. """

        batch = self.service.new_batch_http_request()
        log.debug('inserting {} Google Agenda events for "{}"'.format(len(self.formatted_events), self.school_year))
        with click.progressbar(self.formatted_events, label='Updating events', length=len(self.formatted_events)) as events:
            # Insert events
            for event in events:
                try:
                    insert_step = self.service.events().insert(
                        calendarId=self.google_calendar_id,
                        body=event, sendNotifications=True
                    )
                    batch.add(insert_step)
                except HttpError as err:
                    raise err
            batch.execute()

