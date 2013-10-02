from .base import Controller

from briefmetrics import api

class ReportController(Controller):

    def index(self):
        user = api.account.get_user(self.request, required=True, joinedload='account')
        g = api.google.auth_session(self.request, user.account.oauth_token)
        r = g.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles')
        r.raise_for_status()

        self.c.result = r.json()

        return self._render('report.mako')
