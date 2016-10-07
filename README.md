## `chronos`

Basic tool to download a CELCAT XML schedule, parse it and send data through [__Google Agenda API__](https://developers.google.com/google-apps/calendar/).

Script `chronos` access schedule from a CELCAT link, XML data and all events are extracted with *BeautifulSoup*. 
Then they are formated into JSON and sent by batch HTTP requests through Google Agenda API. A POST request is done on a Slack incoming webhook to publish a new message on a defined channel (to tell students that schedule has been updated).

Environment variables must be defined in a `.env` file at root of the project.


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