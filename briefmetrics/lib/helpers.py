"""Helper functions

This module is available as the ``h`` variable in templates, and can also be
imported into handler modules or elsewhere. Put any common functions you want
to access in all templates here. Helpers are normally functions that format
data for output or perform simple calculations. If your objects would never
be called from a template, they're not helpers and you should create a separate
module under 'lib' for them. If you have helpers that are module-sized,
put them in a module under 'lib' and import them here, or import them directly
into the templates and views that need them.

The template globals (``h`` et al) are set in
``briefmetrics/web/environment.py``.
"""

import re
from urllib import urlencode

from unstdlib import html, slugify
from pyramid.asset import abspath_from_asset_spec  # TODO: Adopt this into unstdlib?

from .gcharts import chart

def stylesheet_link(request, asset_spec):
    real_path = abspath_from_asset_spec(asset_spec)
    url_path = request.static_path(asset_spec)
    return html.stylesheet_link(url_path, real_path, cache_bust='md5')


def javascript_link(request, asset_spec):
    real_path = abspath_from_asset_spec(asset_spec)
    url_path = request.static_path(asset_spec)
    return html.javascript_link(url_path, real_path, cache_bust='md5')


literal = html.literal


def text_if(cond, text):
    if cond:
        return html.literal(text)
    return ''

RE_HUMAN_URL = re.compile('^(\w*://)?(www\.)?(.+)/?$')

def human_url(s):
    m = RE_HUMAN_URL.match(s)
    return m and m.group(3)

def human_link(href, attrs=None):
    if '://' not in href:
        href = 'http://' + href

    return html.tag('a', human_url(href), attrs={'href': href})

def num_ordinal(n): # lol
    return 'th' if 11 <= n <=13 else {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th')

def human_date(d):
    return d.strftime('%A %b ') + str(d.day) + num_ordinal(d.day)

def human_time(seconds=None):
    r = []
    rem = 0
    for div, unit in [(3600.0, 'hr'), (60.0, 'min'), (1.0, 'sec')]:
        rem = seconds % div
        v = (seconds - rem) / div
        if not v:
            continue
        r.append('%d%s' % (v, unit))

    return ' '.join(r)

def human_int(n):
    return '{:,}'.format(int(n))

def ga_permalink(section, report, date_start=None, date_end=None):
    awp = "a{accountId}w{internalWebPropertyId}p{id}".format(**report.remote_data)
    r = "https://www.google.com/analytics/web/#" + section + "/" + awp + "/"

    params = {}
    if date_start:
        params['_u.date00'] = date_start.strftime('%Y%m%d')
    if date_end:
        params['_u.date01'] = date_end.strftime('%Y%m%d')

    if params:
        r += '?' + urlencode(params)

    return r
