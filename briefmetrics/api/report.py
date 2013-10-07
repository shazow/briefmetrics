import datetime

from briefmetrics.lib.controller import Controller, Context
from briefmetrics.lib.gcharts import encode_rows

from . import google as api_google


def fetch_weekly(request, report, date_start):
    date_end = date_start + datetime.timedelta(days=6)

    oauth = api_google.auth_session(request, report.account.oauth_token)
    q = api_google.Query(oauth)

    c = Context(report=report, date_start=date_start, date_end=date_end)
    c.base_url = report.remote_data.get('websiteUrl', '')
    c.date_next = date_start + datetime.timedelta(days=7)
    c.subject = "Weekly report for %s" % report.display_name

    params = {
        'id': report.remote_data['id'],
        'date_start': date_start,
        'date_end': date_end,
    }

    c.report_summary = q.report_summary(**params)
    c.report_referrers = q.report_referrers(**params)
    c.report_pages = q.report_pages(**params)
    c.report_social = q.report_social(**params)

    r = q.report_historic(**params)
    c.historic_data = encode_rows(r.get('rows', []))

    return c


def render_weekly(request, user, context):
    context.user = user

    return Controller(request, context=context)._render_template('report.mako')
