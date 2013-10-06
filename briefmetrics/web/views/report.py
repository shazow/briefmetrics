from unstdlib import now
import datetime

from .base import Controller

from briefmetrics import api

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

        return self._render('report.mako')
