from briefmetrics.lib.report import DailyMixin
from .base import GAReport


class DailyReport(DailyMixin, GAReport):
    id = 'day'
    label = 'Alerts (Daily)'

    template = 'email/report/daily.mako'

    def fetch(self, google_query):
        pass


