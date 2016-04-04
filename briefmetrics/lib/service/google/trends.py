import datetime
from briefmetrics.lib.table import Column
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib import helpers as h

from briefmetrics.lib.report import (
    MonthlyMixin,
    cumulative_by_month,
)
from .base import GAReport
from .helpers import (
    _cast_time,
    _cast_percent,
    _cast_title,
    _format_percent,
    _prune_abstract,
)



class TrendsReport(MonthlyMixin, GAReport):
    "Monthly report"
    id = 'month'
    label = 'Trends (Monthly)'

    template = 'email/report/monthly.mako'

    def fetch(self, google_query):
        last_month_date_start = (self.date_start - datetime.timedelta(days=self.date_start.day + 1)).replace(day=1)

        # Summary
        summary_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:users', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgSessionDuration', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            Column('ga:bounceRate', label='Bounce Rate', type_cast=_cast_percent, type_format=_format_percent, reverse=True, threshold=0),
        ]
        self.tables['summary'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': last_month_date_start, # Extra month
                'end-date': self.date_end,
                'sort': '-ga:yearMonth',
            },
            dimensions=[
                Column('ga:yearMonth'),
            ],
            metrics=summary_metrics + [Column('ga:sessions', type_cast=int)],
        )

        self.tables['geo'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:users',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:country', label='Country', visible=1, type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['device'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:users',
            },
            dimensions=[
                Column('ga:deviceCategory', label='Device', visible=1, type_cast=_cast_title),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['browser'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:users',
            },
            dimensions=[
                Column('ga:browser', label='Browser', visible=1),
            ],
            metrics=[col.new() for col in summary_metrics] + [
                Column('ga:avgPageLoadTime', label='Load Time', type_cast=float),
            ],
        )

        self.tables['geo'].tag_rows()
        self.tables['device'].tag_rows()
        self.tables['browser'].tag_rows()


        # TODO: Add last year's month

        historic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': last_month_date_start,
                'end-date': self.date_end,
            },
            dimensions=[
                Column('ga:date'),
                Column('ga:yearMonth', visible=0),
            ],
            metrics=[
                Column('ga:pageviews', label='Views', type_cast=int, visible=1),
                Column('ga:users', label='Uniques', type_cast=int),
            ],
        )

        intro_config = self.config.get('intro')
        if intro_config:
            # For John Sheehan
            historic_table.set_visible('ga:yearMonth', intro_config)

        iter_historic = historic_table.iter_visible()
        _, views_column = next(iter_historic)
        monthly_data, max_value = cumulative_by_month(iter_historic)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['current_month'] = self.date_start.strftime('%B')
        self.data['last_month'] = last_month_date_start.strftime('%B')
        self.data['current_month_days'] = self.date_end.day
        self.data['last_month_days'] = (self.date_start - datetime.timedelta(days=1)).day
