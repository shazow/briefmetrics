from urllib import urlencode
from random import randint
from itertools import groupby

from unstdlib.html import literal


API_URL = 'http://%d.chart.apis.google.com/chart'

def chart(encoded_data, width=250, height=100):
    if not encoded_data:
        return ''

    params = {
        'chs': '{0}x{1}'.format(width, height),
        'chd': encoded_data,
        'cht': 'ls',
        'chco': 'ffffff00|9c1a32|ffffff00',
        'chm': 'B,CE234233,0,0,0|B,CE234277,1,0,0,1|B,CE234240,2,0,0,2',
    }
    url = API_URL % randint(0,9)

    return literal('<img src="{0}?{1}" style="width: {2}px; height: {3}px" alt="Chart" />'.format(url, urlencode(params), width, height))


def encode_value(n, div, max_value, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-.'):
    if n is None:
        return '__'

    n *= max_value / div
    return '%s%s' % (alphabet[int(float(n) / 64)], alphabet[int(n % 64)])

def encode_rows(rows, max_value=4095, month_idx=1, value_idx=2):
    if not rows:
        return

    size = 0
    div = 0
    sum = 0

    months = []

    for month_num, data in groupby(rows, lambda r: r[month_idx]):
        rows = []
        for row in data:
            rows.append(sum)
            sum += float(row[value_idx])

        rows.append(sum)
        div = max(div, sum)
        sum = 0

        # Pad?
        num_rows = len(rows)
        if num_rows < size:
            rows += [None] * (size - num_rows)
        else:
            size = num_rows

        months.append(rows)

    div = div or 1
    max_value = min(max_value, div)

    return 'e:' + ','.join(
        ''.join(
            encode_value(value, div, max_value) for value in month
        ) for month in months)
