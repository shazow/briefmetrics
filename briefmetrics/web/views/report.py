from .base import Controller

from briefmetrics import api

class ReportController(Controller):

    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='account.reports')

        if not user.account.reports:
            self.request.flash('Select a profile.')
            return self._redirect(self.request.route_path('settings'))


        report = user.account.reports[0]
        oauth = api.google.oauth_session(self.request, user.account.oauth_token)
        self.result = api.google.report_summary(oauth, report)

        return self._render('report.mako')
