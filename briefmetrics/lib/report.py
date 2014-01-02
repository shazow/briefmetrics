from collections import OrderedDict
import datetime

from .gcharts import encode_rows
from . import helpers as h
from .table import Table, Column


def _prune_abstract(label):
    if label.startswith('('):
        return
    return label

def _cast_bounce(v):
    v = float(v or 0.0) / 100.0
    if v:
        return v

def _cast_time(v):
    v = float(v or 0.0)
    if v:
        return v


class EmptyReportError(Exception):
    pass


class Report(object):
    template = 'email/report/daily.mako'

    def __init__(self, report, since_time):
        self.data = {}
        self.tables = {}
        self.report = report
        self.owner = report.account and report.account.user
        self.remote_id = report.remote_id
        self.messages = []

        base_url = self.report.remote_data.get('websiteUrl', '')
        if base_url and 'http://' not in base_url:
            base_url = 'http://' + base_url

        if not self.remote_id:
            # TODO: Remove this after backfill
            self.remote_id = report.remote_id = report.remote_data['id']

        self.base_url = self.report.remote_data.get('websiteUrl', '')

        self.since_time = since_time
        self.date_start, self.date_end, self.date_next = self.get_date_range(since_time)

    @classmethod
    def create_from_now(cls, report, now):
        # TODO: Take into account preferred time.
        date_start = now.date()
        return cls(report, date_start)

    def get_date_range(self, since_time):
        """
        Returns a (start, end, next) date tuple.
        """
        date_start = (since_time - datetime.timedelta(days=1)).date()
        date_end = date_start
        date_next = self.report.next_preferred(date_end).date()

        return date_start, date_end, date_next

    def get_subject(self):
        return u"Report for {site} ({date})".format(
            date=self.date_start.strftime('%b {}').format(self.date_start.day),
            site=self.report.display_name,
        )

    def get_query_params(self):
        return {
            'id': self.remote_id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }

    def build(self):
        pass


class WeeklyReport(Report):
    template = 'email/report/weekly.mako'

    def get_date_range(self, since_time):
        # Last Sunday
        date_start = since_time.date() - datetime.timedelta(days=6) # Last week
        date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week
        date_end = date_start + datetime.timedelta(days=6)
        date_next = self.report.next_preferred(date_end + datetime.timedelta(days=7)).date()

        return date_start, date_end, date_next

    def get_subject(self):
        if self.date_start.month == self.date_end.month:
            return u"Report for {site} ({date})".format(
                date=self.date_start.strftime('%b {}-{}').format(self.date_start.day, self.date_end.day),
                site=self.report.display_name,
            )

        return u"Report for {site} ({date_start}-{date_end})".format(
            date_start=self.date_start.strftime('%b {}').format(self.date_start.day),
            date_end=self.date_end.strftime('%b {}').format(self.date_end.day),
            site=self.report.display_name,
        )

    def _cumulative_by_month(self, month_views_iter):
        months = OrderedDict()
        max_value = 0
        for month, views in month_views_iter:
            month_list = months.get(month)
            if not month_list:
                month_list = months[month] = []
                last_val = 0
            else:
                last_val = month_list[-1]
            val = last_val + views
            month_list.append(val)
            max_value = max(max_value, val)

        return months.values(), max_value

    def fetch(self, google_query):

        # Summary
        summary_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:visitors', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgTimeOnSite', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            Column('ga:visitBounceRate', label='Bounce Rate', type_cast=_cast_bounce, type_format=h.human_percent, reverse=True, threshold=0),
        ]
        self.tables['summary'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start - datetime.timedelta(days=7), # Extra week
                'end-date': self.date_end,
                'sort': '-ga:week',
            },
            dimensions=[
                Column('ga:week'),
            ],
            metrics=summary_metrics + [Column('ga:visits', type_cast=int)],
        )

        # Pages
        # TODO: Add ga:avgPageLoadTime 
        self.tables['pages'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:pageviews',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:pagePath', label='Pages', visible=1, type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        if not self.tables['pages'].rows:
            # TODO: Use a better short circuit?
            raise EmptyReportError()

        self.tables['referrers'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'filters': 'ga:medium==referral',
                'sort': '-ga:pageviews',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:fullReferrer', label='Referrer', visible=1, type_cast=_prune_abstract)
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        date_start_last_month = self.date_end - datetime.timedelta(days=self.date_end.day)
        date_start_last_month -= datetime.timedelta(days=date_start_last_month.day - 1)

        self.tables['organic'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'filters': 'ga:medium==organic;ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:source', type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['social'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:pageviews',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:socialNetwork', type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        historic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start_last_month,
                'end-date': self.date_end,
            },
            dimensions=[
                Column('ga:date'),
                Column('ga:month', visible=0),
            ],
            metrics=[
                Column('ga:pageviews', label='Views', type_cast=int, visible=1),
                Column('ga:visitors', label='Uniques', type_cast=int),
            ],
        )

        intro_config = self.report.config.get('intro')
        if intro_config:
            # For John Sheehan
            historic_table.set_visible('ga:month', intro_config)

        iter_historic = historic_table.iter_visible()
        _, views_column = next(iter_historic)
        monthly_data, max_value = self._cumulative_by_month(iter_historic)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[len(current_month)-1]

        t = Table(columns=[
            Column('source', label='Social & Search', visible=1),
        ] + [col.new() for col in summary_metrics])

        for cells in self.tables['social'].iter_rows():
            t.add(cells)

        for cells in self.tables['organic'].iter_rows():
            t.add(cells)

        t.sort(reverse=True)
        self.tables['social_search'] = t

        self.tables['social_search'].tag_rows()
        self.tables['referrers'].tag_rows()
        self.tables['pages'].tag_rows()


class DailyReport(Report):
    template = 'email/report/daily.mako'

    def fetch(self, google_query):
        pass


class MonthlyReport(Report):
    template = 'email/report/monthly.mako'

    def get_date_range(self, since_time):
        since_start = since_time.date().replace(day=1)
        date_end = since_start - datetime.timedelta(days=1) # Last of the previous month
        date_start = date_end.replace(day=1) # First of the previous month
        date_next = self.report.next_preferred(since_start).date()

        return date_start, date_end, date_next

    def get_subject(self):
        return u"Report for {site} ({date})".format(
            date=self.date_start.strftime('%B'),
            site=self.report.display_name,
        )

    def fetch(self, google_query):
        date_start_last_month = (self.date_start - datetime.timedelta(days=self.date_start.day + 1)).replace(day=1)

        # Summary
        summary_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:visitors', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgTimeOnSite', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            Column('ga:visitBounceRate', label='Bounce Rate', type_cast=_cast_bounce, type_format=h.human_percent, reverse=True, threshold=0),
        ]
        self.tables['summary'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start_last_month, # Extra month
                'end-date': self.date_end,
                'sort': '-ga:month',
            },
            dimensions=[
                Column('ga:month'),
            ],
            metrics=summary_metrics + [Column('ga:visits', type_cast=int)],
        )

        self.tables['geo'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:visitors',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:country', label='Country', visible=1),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['device'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:visitors',
            },
            dimensions=[
                Column('ga:deviceCategory', label='Device', visible=1),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['browser'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:visitors',
            },
            dimensions=[
                Column('ga:browser', label='Device', visible=1),
            ],
            metrics=[col.new() for col in summary_metrics] + [Column('ga:avgPageLoadTime', label='Load Time', visible=1)],
        )


        # TODO: Add last year's month

        historic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start_last_month,
                'end-date': self.date_end,
            },
            dimensions=[
                Column('ga:date'),
                Column('ga:month', visible=0),
            ],
            metrics=[
                Column('ga:pageviews', label='Views', type_cast=int, visible=1),
                Column('ga:visitors', label='Uniques', type_cast=int),
            ],
        )

        intro_config = self.report.config.get('intro')
        if intro_config:
            # For John Sheehan
            historic_table.set_visible('ga:month', intro_config)

        iter_historic = historic_table.iter_visible()
        _, views_column = next(iter_historic)
        monthly_data, max_value = self._cumulative_by_month(iter_historic)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[len(current_month)-1]
