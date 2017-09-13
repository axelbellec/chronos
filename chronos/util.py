""" Common methods to download or read files. """

import json
import yaml

import requests
import tqdm


def download_file(url, output_filename):
    response = requests.get(url, stream=True)

    assert response.status_code == 200

    with open(output_filename, 'wb') as output_file:
        for data in tqdm.tqdm(response.iter_content()):
            output_file.write(data)


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

