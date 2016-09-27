import re

import datetime as dt
import lxml
from bs4 import BeautifulSoup

from util import datetime_to_ics, download_file, read_xml, ICS_Event

URL = 'https://edt.univ-tlse3.fr/FSI/FSImentionM/MathAppli/g28755.xml'
XML_FILE = 'edt.xml'

# ICS constants
ICS_HEADER = 'BEGIN:VCALENDAR\nX-WR-CALNAME:M2 MAT-SID\nX-WR-TIMEZONE:Europe/Paris\n'
ICS_FOOTER = 'END:VCALENDAR'


def main():
    # Download schedule
    download_file(URL, XML_FILE)

    # Read XML data
    xml_data = read_xml(XML_FILE)

    # Give it to Beautiful Soup for pretty parsing
    soup = BeautifulSoup(xml_data, "html.parser")

    # Compute a correspondance tables between 'rawweeks' and the first weekday
    dates = {span.alleventweeks.get_text(): span['date'] for span in soup.find_all('span')}

    with open('edt.ics', 'w') as f:
        f.write(ICS_HEADER)

        for event in soup.find_all('event'):
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
            dtstart = datetime_to_ics(dt.datetime.strptime(start, '%d/%m/%Y-%H:%M') + dt.timedelta(days=nday))
            dtend = datetime_to_ics(dt.datetime.strptime(end, '%d/%m/%Y-%H:%M') + dt.timedelta(days=nday))

            ics_event = ICS_Event(
                location=room,
                summary='({}) - {}'.format(category, name),
                description=group,
                dtstart=dtstart,
                dtend=dtend
            )
            f.write(ics_event.bloc() + '\n')

        f.write(ICS_FOOTER)

if __name__ == '__main__':
    main()
