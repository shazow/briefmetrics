import datetime
from briefmetrics.lib.table import Table, Column
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib import helpers as h

from briefmetrics.lib.report import (
    EmptyReportError,
    WeeklyMixin,
    inject_table_delta,
    cumulative_by_month,
)
from .base import GAReport
from .helpers import (
    _cast_time,
    _cast_percent,
    _cast_title,
    _format_dollars,
    _format_percent,
    _prune_abstract,
    _prune_referrer,
)


class MobileWeeklyReport(WeeklyMixin, GAReport):
    id = 'mobile-week'
    label = 'Weekly (Mobile)'

    template = 'email/report/mobile-weekly.mako'

    def get_preview(self):
        if len(self.tables['summary'].rows) < 2:
            return u''

        primary_metric = self.report.config.get('intro') or 'ga:users'
        this_week, last_week = (r.get(primary_metric) for r in self.tables['summary'].rows[:2])
        delta = (this_week / float(last_week or 1.0)) - 1
        return u"Your app had {this_week} this {interval} ({delta} over last {interval}).".format(
            this_week=h.format_int(this_week, self.data['total_units']),
            delta=h.human_percent(delta, signed=True),
            interval=self.data.get('interval_label', 'week'),
        )

    def _get_search_keywords(self, google_query, interval_field):
        t = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start, # Extra week
                'end-date': self.date_end,
                'sort': '-{},-ga:users'.format(interval_field),
                'filters': 'ga:keyword!=(not provided);ga:medium==organic',
                'max-results': '5',
            },
            dimensions=[
                Column(interval_field),
                Column('ga:keyword', label='Search Keywords', type_cast=_prune_abstract, visible=1),
            ],
            metrics=[
                Column('ga:users', label='Users', type_cast=int, type_format=h.human_int, visible=0, threshold=0),
                Column('ga:avgSessionDuration', label='Session', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            ],
        )
        t.set_visible('ga:users', 'ga:keyword')
        #split_table_delta(t, split_column=interval_field, join_column='ga:keyword', compare_column='ga:sessions')
        #t.sort(reverse=True)
        #t.limit(10)
        return t

    def _get_ecommerce(self, google_query, interval_field, limit=10):
        t = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                #'start-date': self.previous_date_start, # Extra week
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-{}'.format(interval_field),
            },
            dimensions=[
                Column(interval_field),
                Column('ga:productName', label="Product", visible=1),
            ],
            metrics=[
                Column('ga:itemRevenue', label="Revenue", type_cast=float, type_format=_format_dollars, visible=0, threshold=0),
                Column('ga:itemQuantity', label="Sales", type_cast=int, type_format=h.human_int),
            ],
        )
        t.sort(reverse=True)

        # Add a limit row
        sum_columns = t.column_to_index['ga:itemRevenue'], t.column_to_index['ga:itemQuantity']
        if len(t.rows) > limit:
            extra, t.rows = t.rows[limit-1:], t.rows[:limit-1]
            values = extra[0].values[:]
            for row in extra[1:]:
                for col_idx in sum_columns:
                    values[col_idx] += row.values[col_idx]

            values[t.column_to_index['ga:productName']] = "(%s)" % h.format_int(len(extra), u"{:,} other product")
            t.add(values)

        idx_sales = t.column_to_index['ga:itemQuantity']
        for row in t.rows:
            v = row.values[idx_sales]
            row.tag(h.format_int(v, u"{:,} Sale"))

        # Add total row
        #row = t.rows[-1].values[:]
        #row[t.column_to_index['ga:itemRevenue']] = t.get('ga:itemRevenue').sum
        #row[t.column_to_index['ga:productName']] = '(total)'
        #t.add(row)

        # Old work from extra week mode
        #split_table_delta(t, interval_field, 'ga:productName', 'ga:itemRevenue')

        return t

    def _get_goals(self, google_query, interval_field):
        goals_api = 'https://www.googleapis.com/analytics/v3/management/accounts/{accountId}/webproperties/{webPropertyId}/profiles/{profileId}/goals'
        r = google_query.get(goals_api.format(profileId=self.remote_data['id'], **self.remote_data))
        has_goals = r.get('items') or []
        goal_metrics = [
            Column('ga:goal{id}Completions'.format(id=g['id']), label=g['name'], type_cast=float)
            for g in has_goals if g.get('active')
        ]

        if not goal_metrics:
            return

        # Note: max 10 metrics allowed
        metrics = goal_metrics[-9:] + [Column('ga:sessions', type_cast=int)]
        raw_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start, # Extra week
                'end-date': self.date_end,
                'sort': '-{}'.format(interval_field),
            },
            metrics=metrics,
            dimensions=[
                Column(interval_field),
            ],
        )

        if len(raw_table.rows) != 2:
            # Less than 2 weeks of data available
            return

        t = Table(columns=[
            Column('goal', label='Goals', visible=1, type_cast=_cast_title),
            Column('completions', label='Events', visible=0, type_cast=int, type_format=h.human_int, threshold=0),
        ])

        num_sessions, num_sessions_last = [next(v) for v in raw_table.iter_rows('ga:sessions')]

        this_week, last_week = raw_table.rows
        col_compare = t.get('completions')
        col_compare_delta = Column('%s:delta' % col_compare.id, label='Events', type_cast=float, type_format=h.human_delta, threshold=0)
        has_completions = False
        for col_id, pos in raw_table.column_to_index.items():
            col = raw_table.columns[pos]
            if not col.id.startswith('ga:goal'):
                continue

            completions, completions_last = this_week.values[pos], last_week.values[pos]
            percent_completions, percent_completions_last = completions*100.0/num_sessions, completions_last*100.0/num_sessions_last
            row = t.add([col.label, completions])
            if not row:
                # Boring
                continue

            if completions > 0:
                row.tag(type="Conversion", value=_format_percent(percent_completions))

            if completions + completions_last > 0:
                has_completions = True
                # Old method:
                # delta = (percent_completions - percent_completions_last) / 100.0
                # New method (same as GA shows):
                delta = completions / completions_last - 1 if completions_last > 0.0 else 1.0
                if abs(delta) > 0.001:
                    row.tag(type='delta', value=delta, column=col_compare_delta, is_positive=delta>0)

        if not has_completions:
            return

        t.sort(reverse=True)

        return t

    def _get_versions(self, google_query, summary_metrics):
        t = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:appVersion',
                'max-results': '50',
            },
            dimensions=[
                Column('ga:appVersion', label='Version', visible=1),
                Column('ga:operatingSystem', label='Operating System', visible=2),
            ],
            metrics=[col.new() for col in summary_metrics],
        )
        t.set_visible('ga:users', 'ga:appVersion')
        t.tag_rows()

        total = float(t.get('ga:users').sum)

        t2 = Table(columns=[
            Column('users', label='Users', visible=0, type_format=_format_percent),
            Column('version', label='Version', visible=1),
        ])

        latest_version = None
        for i, (users, version, os) in enumerate(t.iter_rows('ga:users', 'ga:appVersion', 'ga:operatingSystem')):
            row = t2.add([users*100.0/total, u"%s on %s" % (version, os)])
            row.tags = t.rows[i].tags
            if not latest_version:
                latest_version = version
            if latest_version == version:
                row.tag('latest')

        t2.limit(5)
        t2.sort(reverse=True)
        return t2

    def fetch(self, google_query):
        days_delta = (self.date_end - self.date_start).days
        is_year_delta = days_delta > 360

        interval_field = 'ga:nthWeek'
        if is_year_delta:
            interval_field = 'ga:year'
        elif days_delta > 6:
            interval_field = 'ga:nthMonth'

        # Summary
        summary_params = {
            'ids': 'ga:%s' % self.remote_id,
            'start-date': self.previous_date_start, # Extra week
            'end-date': self.date_end,
            'sort': '-{}'.format(interval_field),
        }
        summary_dimensions = [
            Column(interval_field),
        ]
        basic_metrics = [
            Column('ga:screenviews', label='Views', type_cast=int, type_format=h.human_int),
            Column('ga:sessions', label='Sessions', type_cast=int, type_format=h.human_int),
            Column('ga:users', label='Users', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:avgSessionDuration', label='Session', type_cast=_cast_time, type_format=h.human_time, threshold=0),
        ]
        summary_metrics = basic_metrics + [
            Column('ga:goalConversionRateAll', label='Conversion', type_cast=float, type_format=_format_percent, threshold=0.1),
            Column('ga:itemRevenue', label="Revenue", type_cast=float, type_format=_format_dollars),
            Column('ga:itemQuantity', label="Sales", type_cast=int, type_format=h.human_int),
        ]
        self.tables['summary'] = summary_table = google_query.get_table(
            params=summary_params,
            dimensions=summary_dimensions,
            metrics=summary_metrics,
        )

        if not summary_table.has_value('ga:users'):
            raise EmptyReportError()

        include_ads = self.config.get('ads') or summary_table.has_value('ga:itemRevenue')

        # Ads
        # FIXME: Merge this with summary_metrics once https://code.google.com/p/analytics-issues/issues/detail?id=693 is fixed.
        if include_ads:
            self.tables['ads'] = google_query.get_table(
                params={
                    'ids': 'ga:%s' % self.remote_id,
                    'start-date': self.date_start,
                    'end-date': self.date_end,
                },
                dimensions=[Column('ga:adGroup')],
                metrics=[
                    Column('ga:adCost', label="Ad Spend", type_cast=float, type_format=_format_dollars, threshold=0),
                    Column('ga:impressions', label="Ad Impressions", type_cast=int, type_format=h.human_int, threshold=0),
                    Column('ga:adClicks', label="Ad Clicks", type_cast=int, type_format=h.human_int, threshold=0),
                    Column('ga:itemRevenue', label="Revenue", type_cast=float, type_format=_format_dollars, threshold=0),
                    Column('ga:itemQuantity', label="Sales", type_cast=int, type_format=h.human_int, threshold=0),
                ],
            )

        # Screens
        screens_metrics = [col.new() for col in basic_metrics]
        if self.config.get('pageloadtime', True):
            screens_metrics += [
                Column('ga:avgPageLoadTime', label='Load', type_cast=float, type_format=h.human_time, reverse=True, threshold=0),
            ]

        self.tables['screens'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:screenviews',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:screenName', label='Screens', visible=1, type_cast=_prune_abstract),
            ],
            metrics=screens_metrics,
        )
        self.tables['screens'].set_visible('ga:screenviews', 'ga:screenName')

        if summary_table.has_value('ga:goalConversionRateAll'):
            # Goals
            self.tables['goals'] = self._get_goals(google_query, interval_field)

        if summary_table.has_value('ga:itemRevenue'):
            # Ecommerce
            self.tables['ecommerce'] = self._get_ecommerce(google_query, interval_field)

        # Historic
        historic_start_date = self.previous_date_start
        if not is_year_delta:
            # Override to just previous month
            historic_start_date = self.date_end - datetime.timedelta(days=self.date_end.day)
            historic_start_date -= datetime.timedelta(days=historic_start_date.day-1)

        # Note: Pace is different from interval, as year pace is still month over month whereas year interval is year over year.
        compare_interval = self.config.get('pace', 'month')
        if compare_interval == 'year' and not is_year_delta:
            historic_start_date = self.date_end - datetime.timedelta(days=self.date_end.day-1)
            historic_start_date = historic_start_date.replace(year=historic_start_date.year-1)

        dimensions = [
            Column('ga:yearMonth', visible=0),
        ]
        if not is_year_delta:
            dimensions += [
                Column('ga:date'),
            ]

        historic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': historic_start_date,
                'end-date': self.date_end,
            },
            dimensions=dimensions,
            metrics=[
                Column('ga:users', label='Users', type_cast=int, visible=1),
                Column('ga:sessions', label='Sessions', type_cast=int),
            ],
        )

        intro_config = self.config.get('intro')
        if intro_config:
            # For John Sheehan
            historic_table.set_visible('ga:yearMonth', intro_config)

        iter_historic = historic_table.iter_visible()
        _, views_column = next(iter_historic)

        if is_year_delta:
            iter_historic = ((mo[:4], v) for mo, v in iter_historic)
        elif compare_interval == 'year':
            mo_filter = u'{d.month:02d}'.format(d=historic_start_date)
            iter_historic = ((mo, v) for mo, v in iter_historic if mo.endswith(mo_filter))

        monthly_data, max_value = cumulative_by_month(iter_historic)
        last_month, current_month = monthly_data[-2:]

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[min(len(current_month), len(last_month))-1]
        self.data['total_last_date_start'] = historic_start_date

        self.tables['search_keywords'] = self._get_search_keywords(google_query, interval_field=interval_field)
        self.tables['search_keywords'].tag_rows()

        self.tables['geo'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:users',
                'max-results': '5',
            },
            dimensions=[
                Column('ga:country', label='Country', visible=1, type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )
        self.tables['versions'] = self._get_versions(google_query, summary_metrics)

        self.tables['geo'].tag_rows()
        self.tables['screens'].tag_rows()
