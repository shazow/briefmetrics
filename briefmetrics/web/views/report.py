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

        self.c.result = api.google.Query(oauth).report_summary(
            id=report.remote_data['id'],
            date_start='2012-01-01',
            date_end='2012-01-07',
        )

        return self._render('report.mako')
