import re
import unicodedata


def strip_accents(text):
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)


def remove_multi_spaces(text):
    return re.sub('\s+', ' ', text)


def preserve_line_breaks_into_words(text):
    re1 = '(?<!\w)\n|\n(?!\w)'
    re2 = '(?<!\/)\n|\n(?!\w)'
    re3 = '(?<!\w)\n|\n(?!\/)'
    regex = re.compile(re1 + re2 + re3)
    return regex.sub('', text)
