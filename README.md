## :date: `chronos`

Basic tool to download a CELCAT XML schedule, parse it and send data through [__Google Agenda API__](https://developers.google.com/google-apps/calendar/).

Script `chronos` access schedule from a CELCAT link, XML data and all events are extracted with *BeautifulSoup*. 
Then they are formated into JSON and sent by batch HTTP requests through Google Agenda API. A POST request is done on a Slack incoming webhook to publish a new message on a defined channel (to tell students that schedule has been updated).

Environment variables must be defined in a `.env` file at root of the project like this :
```
# Celcat URL (e.g. `https://edt.univ-tlse3.fr/FSI/FSImentionM/MathAppli/g28755.xml`)
SCHEDULE_URL=<CELCAT_SCHEDULE_URL>
# Google Calendar API credentials
CLIENT_ID=<GOOGLE_CALENDAR_API_CLIENT_ID>
CLIENT_SECRET=<GOOGLE_CALENDAR_API_SECRET_TOKEN>
# Google Agenda ID (e.g. `1knu1vhfrg0o2t6dk9941bl9gs@group.calendar.google.com`)
CALENDAR_ID=<CALENDAR_ID>
# Slack URL is useful to notify students the last update time
SLACK_URL=<SLACK_INCOMING_WEBHOOK_URL>
```


### Requirements

```
pip install -r requirements.txt
```

### Usage

```
python chronos.py --delete --insert --alert
```

### Options

```
Usage: chronos.py [OPTIONS]

Options:
  --force / --no-force    Force schedule update
  --delete / --no-delete  Delete all old events
  --insert / --no-insert  Insert all new events
  --alert / --no-alert    Push alert to Slack channel
  --help                  Show this message and exit.
```

### Managing `crontab`

Automate task every five minutes and send a ping to [__HealthChecks.io__](https://healthchecks.io/checks/).
```
## Chronos
*/5 * * * * cd <repo_directory> && ./venv/bin/python chronos.py --no-force --delete --insert --alert && curl https://hchk.io/<task_id>
```