# coding: utf-8

""" Common methods to download or read files. """

import json
import yaml

import requests
import click


def download_file(url, output_filename):
    response = requests.get(url, stream=True)
    assert response.status_code == 200

    with open(output_filename, 'wb') as output_file:
        content = list(response.iter_content())
        with click.progressbar(content, length=len(content), label='Downloading timetable XML file') as bar:
            for chunk in bar:
                output_file.write(chunk)


def read_xml(file):
    with open(file, 'r') as stream_file:
        content = stream_file.read()
    return content


def read_json(file):
    with open(file, 'r') as stream_file:
        return json.load(stream_file)


def read_yaml(file):
    with open(file, 'r') as stream_file:
        return yaml.load(stream_file)


def write_json(file, data):
    with open(file, 'w') as stream_file:
        stream_file.write(data)

