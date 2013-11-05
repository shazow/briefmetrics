import datetime
from .controller import DefaultContext


class Report(object):
    __slots__ = (
        'base_url',
        'date_end',
        'date_next',
        'date_start',
        'owner',
        'remote_id',
        'report',
        'data',
    )

    def __init__(self, report, date_start):
        self.data = DefaultContext()
        self.report = report
        self.owner = report.account and report.account.user
        self.remote_id = report.remote_id

        if not self.remote_id:
            # TODO: Remove this after backfill
            self.remote_id = report.remote_id = report.remote_data['id']

        self.base_url = self.report.remote_data.get('websiteUrl', '')

        self.date_start = date_start
        self.date_end = date_start
        self.date_next = report.next_preferred(self.date_end).date()

    @classmethod
    def create_from_now(cls, report, now):
        # TODO: Take into account preferred time.
        date_start = now.date()
        return cls(report, date_start)

    def get_subject(self):
        return u"Report for %s: %s" % (
            self.date_start.strftime('%b {}').format(self.date_start.day),
            self.report.display_name,
        )

    def get_query_params(self):
        return {
            'id': self.remote_id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }


class WeeklyReport(Report):
    def __init__(self, report, date_start):
        super(WeeklyReport, self).__init__(report, date_start)

        # FIXME: This gets called twice in this model :(
        self.date_end = self.date_start + datetime.timedelta(days=6)
        self.date_next = report.next_preferred(self.date_end + datetime.timedelta(days=7)).date()

    def get_subject(self):
        if self.date_start.month == self.date_end.month:
            return u"Report for %s: %s" % (
                self.date_start.strftime('%b {}-{}').format(self.date_start.day, self.date_end.day),
                self.report.display_name,
            )

        return u"Report for %s-%s: %s" % (
            self.date_start.strftime('%b {}').format(self.date_start.day),
            self.date_end.strftime('%b {}').format(self.date_end.day),
            self.report.display_name,
        )


