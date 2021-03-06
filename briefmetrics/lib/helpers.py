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
from datetime import timedelta
from urllib.parse import urlencode

from unstdlib import html, slugify, get_many, now
from pyramid.asset import abspath_from_asset_spec  # TODO: Adopt this into unstdlib?
from .gcharts import chart

_Default = object()

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

def human_url(s, max_length=None):
    if not s:
        return ''

    m = RE_HUMAN_URL.match(s)
    r = m.group(3) if m else s
    r = r.strip('/')
    return truncate(r, max_length=max_length)

def human_link(href, label=None, attrs=None, max_length=None):
    if not href:
        return label

    if href.startswith('//'):
        href = 'http:' + href
    elif href.startswith('/'):
        return href
    elif ' ' in href:
        return href
    elif '://' not in href:
        if '.' in href:
            href = 'http://' + href
        else:
            return href

    if not label:
        label = human_url(href, max_length=max_length)

    return html.tag('a', label, attrs={'href': href})

def num_ordinal(n): # lol
    return 'th' if 11 <= n <=13 else {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th')

def human_date(d, max_unit='month'):
    if not d:
        return

    f = '{:%A %b {day}}'
    if max_unit == 'year':
        f = '{:%A, %b {day} %Y}'

    return f.format(d, day=str(d.day) + num_ordinal(d.day))

def human_time(seconds):
    if not seconds:
        return '0s'

    r = []
    rem = 0
    for div, unit in [(3600.0, 'hr'), (60.0, 'min')]:
        rem = seconds % div
        v = (seconds - rem) / div
        seconds = rem
        if not v:
            continue
        r.append('%d%s' % (v, unit))

    if seconds:
        if r or seconds >= 10.0 or seconds % 1.0 == 0:
            r.append('%dsec' % seconds)
        else:
            r.append('{:0.3}sec'.format(seconds))

    if not r:
        return '0s'

    return ' '.join(r)

def human_int(n):
    return u'{:,}'.format(int(n or 0))

def human_percent(f, denominator=1.0, signed=False):
    if f is None:
        return ''

    if denominator != 1.0:
        f /= denominator

    # TODO: Write tests
    precision = 1
    fa = abs(f)
    if fa > 1.0:
        precision = 0
    elif (fa * 100) % 1.0 < 0.05:
        precision = 0
    elif fa < 0.1:
        precision = 2

    fmt = u'{:%s0.%d%%}' % ('+' if signed else '', precision)

    return fmt.format(float(f))

def human_delta(f):
    return human_percent(f, signed=True)

def human_dollar(cents, currency=None):
    precision = min(cents % 100, 2)
    f = u'${:,.%df}' % precision
    if currency:
        # TODO: Localize $?
        f += ' %s' % currency.upper()

    return f.format(float(cents)/100.0)

def truncate(s, max_length=80):
    if not max_length or len(s) <= max_length:
        return s
    return s[:max_length-1] + u'\u2026'

def ga_permalink(section, report, date_start=None, date_end=None):
    try:
        awp = "a{accountId}w{internalWebPropertyId}p{id}".format(**report.remote_data)
    except KeyError:
        return ''

    r = "https://www.google.com/analytics/web/#" + section + "/" + awp + "/"

    params = {}
    if date_start:
        params['_u.date00'] = date_start.strftime('%Y%m%d')
    if date_end:
        params['_u.date01'] = date_end.strftime('%Y%m%d')

    if params:
        r += '?' + urlencode(params)

    return r

def format_int(n, singular=_Default, plural=_Default):
    """
    Return `singular.format(n)` if n is 1, or `plural.format(n)` otherwise. If
    plural is not specified, then it is assumed to be same as singular but
    suffixed with an 's'.

    :param n:
        Integer which determines pluralness.

    :param singular:
        String with a format() placeholder for n. (Default: `u"{:,}"`)

    :param plural:
        String with a format() placeholder for n. (Default: If singular is not
        default, then it's `singular + u"s"`. Otherwise it's same as singular.)

    Example: ::

        >>> format_int(1000)
        u'1,000'
        >>> format_int(1, u"{} day")
        u'1 day'
        >>> format_int(2, u"{} day")
        u'2 days'
        >>> format_int(2, u"{} box", u"{} boxen")
        u'2 boxen'
        >>> format_int(20000, u"{:,} box", u"{:,} boxen")
        u'20,000 boxen'
    """
    n = int(n)

    if singular in (None, _Default):
        if plural is _Default:
            plural = None

        singular = u'{:,}'

    elif plural is _Default:
        plural = singular + u's'

    if n == 1 or not plural:
        return singular.format(n)

    return plural.format(n)


RE_HTML_TAGS = re.compile('<[^<]+?>')
RE_TEXT_SPACING = re.compile('\s\s+')

def html_to_text(s, strip_spaces=False):
    s = RE_HTML_TAGS.sub('', s)

    if strip_spaces:
        s = RE_TEXT_SPACING.sub(' ', s.replace('\n', ' ')).strip()

    return s
