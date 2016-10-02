## `ups-schedule-parser`

Basic tool to download a CELCAT XML schedule, parse it and send data through [__Google Agenda API__](https://developers.google.com/google-apps/calendar/).

### Requirements

```
pip install -r requirements.txt
```

### Usage

```
python edt_to_agenda_api.py --delete --insert --alert
```

### Options

```
Usage: edt_to_agenda_api.py [OPTIONS]

Options:
  --force / --no-force    Force schedule update
  --delete / --no-delete  Delete all old events
  --insert / --no-insert  Insert all new events
  --alert / --no-alert    Push alert to Slack channel
  --help                  Show this message and exit.
```