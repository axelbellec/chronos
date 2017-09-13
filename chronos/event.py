""" Events formatter. """


class GoogleCalendarEvent(object):
    """ A Google Calendar Event object formatter. """

    def __init__(self, location=None, summary=None, description=None, dtstart=None, dtend=None):
        self.summary = summary
        self.location = location
        self.summary = summary
        self.description = description
        self.dtstart = dtstart
        self.dtend = dtend

    @property
    def json(self):
        """ Return a JSON formatted event. """
        return {
            'summary': self.summary,
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': self.dtstart,
                'timeZone': 'Europe/Paris',
            },
            'end': {
                'dateTime': self.dtend,
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
