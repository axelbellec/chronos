## `ups-schedule-parser`

Basic tool to download a CELCAT XML schedule, parse it and send data through [__Google Agenda API__](https://developers.google.com/google-apps/calendar/).

### Requirements

```
pip install -r requirements.txt
```

### Usage

```
python edt_to_agenda_api.py --delete --insert
```

### Options

```
python edt_to_agenda_api.py --help
Usage: edt_to_agenda_api.py [OPTIONS]

Options:
  --force / --no-force    Force schedule update
  --delete / --no-delete  Delete all old events
  --insert / --no-insert  Insert all new events
  --help                  Show this message and exit.
```