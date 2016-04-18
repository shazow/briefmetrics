from briefmetrics.lib import helpers as h

def to_display_name(remote_data):
    # FIXME: This is duplicated in briefmetrics.api.report
    name = remote_data.get('displayName') or h.human_url(remote_data.get('websiteUrl')) or remote_data.get('display_name') or remote_data.get('name')
    return h.human_url(name)


## Reports:


def _prune_abstract(v):
    if v.startswith('('):
        return
    return v

def _prune_referrer(v):
    if not v or v.startswith('('):
        return
    return v.replace(' ', '+')

def _cast_percent(v):
    return float(v or 0.0)

def _format_percent(f):
    return h.human_percent(f, denominator=100.0)

def _format_float(f):
    return "%0.1f" % f

def _format_dollars(v):
    return h.human_dollar(v * 100.0)

def _cast_time(v):
    v = float(v or 0.0)
    if v:
        return v

def _cast_title(v):
    # Also prunes abstract
    if not v or v.startswith('('):
        return

    if not v[0].isupper():
        return v.title()

    return v

