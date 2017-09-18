# coding: utf-8

""" Chronos CLI. """

import yaml

from chronos.parser import TimetableParser
from chronos.tracing import log_factory

log = log_factory(__name__)


def cli(force=False):
    """ Basic tool to download CELCAT timetables, 
        parse them and send data through Google Agenda API. 
    """

    with open('config.yml', 'r') as config_file:
        config = yaml.load(config_file)

    for year_group, properties in config.items():
        log.debug('downloading and parsing timetable for "%s"', year_group)
        timetable = TimetableParser(
            school_year=year_group,
            schedule_url=properties['timetable_url'],
            description=properties['description'],
            google_calendar_id=properties['google_calendar_id'],
            force_update=force
        )
        timetable.process()

if __name__ == '__main__':
    cli()
