import datetime
from itertools import groupby

from .base import Controller

from briefmetrics import api

def _encode_value(n, div, max_value, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-.'):
    if n is None:
        return '__'

    n *= max_value / div
    return '%s%s' % (alphabet[int(float(n) / 64)], alphabet[int(n % 64)])

def _encode_chart(rows, max_value=4095, month_idx=1, value_idx=2):
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
            _encode_value(value, div, max_value) for value in month
        ) for month in months)


class ReportController(Controller):

    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='account.reports')

        if not user.account.reports:
            return self._redirect(self.request.route_path('settings'))

        # TODO: Handle arbitrary reports
        report = user.account.reports[0]
        oauth = api.google.auth_session(self.request, user.account.oauth_token)

        # Last monday
        today = datetime.date.today()
        self.c.date_start = today + datetime.timedelta(days=-today.weekday()-1)
        self.c.date_end = self.c.date_start + datetime.timedelta(days=6)
        self.c.date_next = self.c.date_start + datetime.timedelta(days=7)

        print self.c.date_start, self.c.date_end

        params = {
            'id': report.remote_data['id'],
            'date_start': self.c.date_start,
            'date_end': self.c.date_end,
        }

        q = api.google.Query(oauth)

        self.c.user = user
        self.c.report = report
        self.c.base_url = report.remote_data['websiteUrl']

        self.c.report_summary = q.report_summary(**params)
        self.c.report_referrers = q.report_referrers(**params)
        self.c.report_pages = q.report_pages(**params)
        self.c.report_social = q.report_social(**params)

        r = q.report_historic(**params)
        self.c.historic_data = _encode_chart(r.get('rows', []))

        return self._render('report.mako')
