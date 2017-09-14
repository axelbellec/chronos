# coding: utf-8

""" Chronos CLI. """

import click

import yaml

from chronos.parser import TimetableParser


@click.command()
@click.option('--force/--no-force', help='Force schedule update', default=False)
def main(force):
    """ Basic tool to download CELCAT timetables, 
        parse them and send data through Google Agenda API. 
    """

    with open('config.yml', 'r') as config_file:
        config = yaml.load(config_file)

    for year_group, properties in config.items():
        click.secho(properties['description'], fg='yellow', bold=True)
        timetable = TimetableParser(
            school_year=year_group,
            schedule_url=properties['timetable_url'],
            description=properties['description'],
            google_calendar_id=properties['google_calendar_id'],
            force_update=force
        )
        timetable.process()

if __name__ == '__main__':
    main()
