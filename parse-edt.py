import re
import unicodedata

import click
import PyPDF2


def strip_accents(text):
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def remove_multi_spaces(text):
    return re.sub('\s+', ' ', text)


@click.command()
@click.option('--pdf', type=str, help='PDF file to extract text')
def extract_text(pdf):
    pdfFileObj = open(pdf, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    # Extract pdf data to text
    pages = [pdfReader.getPage(index).extractText() for index in range(pdfReader.numPages)]
    data = remove_multi_spaces(strip_accents(''.join(pages).replace('\n', ' ')))

    with open('data.txt', 'w') as f:
        f.write(data)

if __name__ == '__main__':
    extract_text()
