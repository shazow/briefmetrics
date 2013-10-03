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
from unstdlib import html, slugify
from pyramid.asset import abspath_from_asset_spec  # TODO: Adopt this into unstdlib?


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
