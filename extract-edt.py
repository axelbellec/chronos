import click
import PyPDF2

from util import remove_multi_spaces, strip_accents, preserve_line_breaks_into_words


@click.command()
@click.option('--pdf', type=str, help='PDF file to extract text')
def extract_text(pdf):
    pdfFileObj = open(pdf, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    # Extract pdf data to text
    pages = [pdfReader.getPage(index).extractText() for index in range(pdfReader.numPages)]
    data = preserve_line_breaks_into_words(remove_multi_spaces(
        strip_accents(''.join(pages)))).replace('\n', '')

    with open('data.txt', 'w') as f:
        f.write(data)

    return data

if __name__ == '__main__':
    extract_text()
