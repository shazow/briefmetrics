from urllib import urlencode
from unstdlib.html import literal
from random import randint

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
