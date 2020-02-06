import datetime
from briefmetrics.lib.table import Table, Column
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib.exceptions import APIError, TableShapeError
from briefmetrics.lib import helpers as h

from briefmetrics.lib.report import (
    EmptyReportError,
    YearlyMixin,
    QuarterlyMixin,
    MonthlyMixin,
    WeeklyMixin,
    inject_table_delta,
    cumulative_by_month,
    cumulative_splitter,
    date_to_quarter,
    quarter_to_dates,
    iter_quarters,
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
    to_display_name,
)


class ActivityReport(WeeklyMixin, GAReport):
    id = 'week'
    label = 'Weekly'

    template = 'email/report/weekly.mako'

    def get_preview(self):
        if len(self.tables['summary'].rows) < 2:
            return u''

        primary_metric = self.report.config.get('intro') or 'ga:pageviews'
        this_week, last_week = (r.get(primary_metric) for r in self.tables['summary'].rows[:2])
        delta = (this_week / float(last_week or 1.0)) - 1
        return u"Your site had {this_week} this {interval} ({delta} over last {interval}).".format(
            this_week=h.format_int(this_week, self.data['total_units']),
            delta=h.human_percent(delta, signed=True),
            interval=self.data.get('interval_label', 'week'),
        )

    def _get_interval_table(self, google_query, interval_field, params, dimensions=None, metrics=None, _cache_keys=None):
        return google_query.get_table(params=params, dimensions=dimensions, metrics=metrics, _cache_keys=_cache_keys)

    def _get_summary(self, google_query, interval_field, metrics):
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
        return self._get_interval_table(google_query, interval_field,
            params=summary_params,
            dimensions=summary_dimensions,
            metrics=metrics,
        )

    def _get_search_keywords(self, google_query, interval_field):
        t = self._get_interval_table(google_query, interval_field,
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start, # Extra week
                'end-date': self.date_end,
                'sort': '-{},-ga:sessions'.format(interval_field),
                'filters': 'ga:keyword!=(not provided);ga:medium==organic',
                'max-results': '5',
            },
            dimensions=[
                Column(interval_field),
                Column('ga:keyword', label='Search Keywords', type_cast=_prune_abstract, visible=1),
            ],
            metrics=[
                Column('ga:sessions', label='Visits', type_cast=int, type_format=h.human_int, visible=0, threshold=0),
                Column('ga:avgSessionDuration', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
                Column('ga:bounceRate', label='Bounce Rate', type_cast=_cast_percent, type_format=_format_percent, reverse=True, threshold=0),
            ],
        )
        t.set_visible('ga:sessions', 'ga:keyword')
        #split_table_delta(t, split_column=interval_field, join_column='ga:keyword', compare_column='ga:sessions')
        #t.sort(reverse=True)
        #t.limit(10)
        return t

    def _get_social_search(self, google_query, date_start, date_end, summary_metrics, max_results=10):
        organic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start,
                'end-date': date_end,
                'filters': 'ga:medium!=referral;ga:medium!=(not set);ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': str(max_results),
            },
            dimensions=[
                Column('ga:source', type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        social_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start,
                'end-date': date_end,
                'sort': '-ga:pageviews',
                'max-results': str(max_results),
            },
            dimensions=[
                Column('ga:socialNetwork', type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        source_col = Column('source', label='Social & Search & Campaigns', visible=1, type_cast=_cast_title)
        t = Table(columns=[
            source_col,
        ] + [col.new() for col in summary_metrics])

        for cells in social_table.iter_rows():
            t.add(cells)

        for cells in organic_table.iter_rows():
            t.add(cells)

        t.sort(reverse=True)
        return t

    def _get_ecommerce(self, google_query, interval_field, limit=10):
        t = self._get_interval_table(google_query, interval_field,
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start, # Extra week
                'start-date': self.date_start,
                'end-date': self.date_end,
                #'sort': '-{}'.format(interval_field),
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
        raw_table = self._get_interval_table(google_query, interval_field,
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
            percent_completions = completions*100.0/num_sessions if num_sessions else 0.0
            percent_completions_last = completions_last*100.0/num_sessions_last if num_sessions_last else 0.0
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

    def _get_interval_field(self):
        days_delta = (self.date_end - self.date_start).days
        is_year_delta = days_delta > 360
        if is_year_delta:
            return 'ga:year'
        if days_delta > 6:
            return 'ga:nthMonth'
        return 'ga:nthWeek'

    def fetch(self, google_query):
        interval_field = self._get_interval_field()
        is_year_delta = interval_field == 'ga:year'
        is_quarter_delta = interval_field == 'bm:quarter'

        # Summary
        basic_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:users', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgSessionDuration', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            Column('ga:bounceRate', label='Bounce Rate', type_cast=_cast_percent, type_format=_format_percent, reverse=True, threshold=0),
        ]
        summary_metrics = basic_metrics + [
            Column('ga:goalConversionRateAll', label='Conversion', type_cast=float, type_format=_format_percent, threshold=0.1),
            Column('ga:itemRevenue', label="Revenue", type_cast=float, type_format=_format_dollars),
            Column('ga:itemQuantity', label="Sales", type_cast=int, type_format=h.human_int),
        ]
        self.tables['summary'] = summary_table = self._get_summary(google_query, interval_field,
            metrics=summary_metrics + [
                Column('ga:sessions', type_cast=int),
                Column('ga:adClicks', type_cast=int),
            ],
        )

        if not summary_table.has_value('ga:pageviews'):
            raise EmptyReportError()

        include_ads = self.config.get('ads') or summary_table.has_value('ga:adClicks') or summary_table.has_value('ga:itemRevenue')

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

        # Pages
        pages_metrics = [col.new() for col in basic_metrics]
        if self.config.get('pageloadtime', True):
            pages_metrics += [
                Column('ga:avgPageLoadTime', label='Page Load', type_cast=float, type_format=h.human_time, reverse=True, threshold=0),
            ]

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
            metrics=pages_metrics,
        )

        # Referrers

        current_referrers = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'filters': 'ga:medium==referral;ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': '25',
            },
            dimensions=[
                Column('ga:fullReferrer', label='Referrer', visible=1, type_cast=_prune_referrer)
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        last_referrers = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start,
                'end-date': self.previous_date_end,
                'filters': 'ga:medium==referral;ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': '250',
            },
            dimensions=[
                Column('ga:fullReferrer', label='Referrer', visible=1, type_cast=_prune_referrer)
            ],
            metrics=[
                summary_table.get('ga:pageviews').new(),
            ],
        )
        inject_table_delta(current_referrers, last_referrers, join_column='ga:fullReferrer')

        self.tables['referrers'] = current_referrers

        if summary_table.has_value('ga:goalConversionRateAll'):
            # Goals
            try:
                self.tables['goals'] = self._get_goals(google_query, interval_field)
            except APIError:
                # Missing permissions for goals
                pass

        if summary_table.has_value('ga:itemRevenue'):
            # Ecommerce
            self.tables['ecommerce'] = self._get_ecommerce(google_query, interval_field)

        # Historic
        historic_start_date = self.previous_date_start
        if not is_year_delta and not is_quarter_delta:
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

        if is_year_delta:
            iter_historic = ((mo[:4], v) for mo, v in iter_historic)
        elif compare_interval == 'year':
            mo_filter = u'{d.month:02d}'.format(d=historic_start_date)
            iter_historic = ((mo, v) for mo, v in iter_historic if mo.endswith(mo_filter))

        monthly_data, max_value = cumulative_by_month(iter_historic)
        if len(monthly_data) < 2:
            raise ValueError("invalid number of historic months", self.remote_id, historic_table.rows)
        if is_quarter_delta:
            # TODO: This needs to be generalized beyond months at this point, sigh
            monthly_data, max_value = cumulative_splitter(monthly_data, split_on=3)
        last_month, current_month = monthly_data[-2:]

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[min(len(current_month), len(last_month))-1]
        self.data['total_last_date_start'] = historic_start_date

        social_search_table = self._get_social_search(google_query, self.date_start, self.date_end, summary_metrics, max_results=25)
        last_social_search = self._get_social_search(google_query, self.previous_date_start, self.previous_date_end, summary_metrics, max_results=100)
        inject_table_delta(social_search_table, last_social_search, join_column='source')

        self.tables['social_search'] = social_search_table
        if self.config.get('search_keywords'):
            self.tables['search_keywords'] = self._get_search_keywords(google_query, interval_field=interval_field)
            self.tables['search_keywords'].tag_rows()

        if self.config.get('geo'):
            self.tables['geo'] = google_query.get_table(
                params={
                    'ids': 'ga:%s' % self.remote_id,
                    'start-date': self.date_start,
                    'end-date': self.date_end,
                    'sort': '-ga:pageviews',
                    'max-results': '5',
                },
                dimensions=[
                    Column('ga:country', label='Country', visible=1, type_cast=_prune_abstract),
                ],
                metrics=[col.new() for col in summary_metrics],
            )
            self.tables['geo'].tag_rows()


        self.tables['social_search'].tag_rows()
        self.tables['referrers'].sort(reverse=True)
        self.tables['referrers'].tag_rows()
        self.tables['pages'].sort(reverse=True)
        self.tables['pages'].tag_rows()


class ActivityConcatReport(ActivityReport):
    id = 'week-concat'
    label = 'Weekly (Combined)'

    template = 'email/report/weekly-concat.mako'

    def __init__(self, report, since_time, config=None):
        super(ActivityConcatReport, self).__init__(report, since_time, config=config)

        remote_data = report.remote_data['combined']
        contexts = []
        for data in remote_data:
            contexts.append(ActivityReport(report, since_time, remote_data=data, display_name=to_display_name(data)))

        self.contexts = contexts
        self.data = True

    def fetch(self, google_query):
        for context in self.contexts:
            try:
                context.fetch(google_query)
            except EmptyReportError:
                pass

    def build(self):
        for context in self.contexts:
            context.build()

    def get_preview(self):
        primary_metric = self.report.config.get('intro') or 'ga:pageviews'
        assert self.contexts, "ActivityConcatReport with no contexts"

        total_units, interval = None, None
        this_week, last_week = 0, 0
        for context in self.contexts:
            if not context.data or not context.tables.get('summary') or len(context.tables['summary'].rows) < 2:
                continue

            a, b = (r.get(primary_metric) for r in context.tables['summary'].rows[:2])
            this_week += a
            last_week += b
            total_units = context.data.get('total_units', total_units)
            interval = context.data.get('interval_label', interval)

        assert total_units, 'Failed to find valid context: %r' % self.contexts

        delta = (this_week / float(last_week or 1.0)) - 1
        return u"Your {number} combined sites had {this_week} this {interval} ({delta} over last {interval}).".format(
            number=len(self.contexts),
            this_week=h.format_int(this_week, total_units),
            delta=h.human_percent(delta, signed=True),
            interval=interval or 'week',
        )



class ActivityMonthlyReport(MonthlyMixin, ActivityReport):
    "Monthly report"
    id = 'activity-month'
    label = 'Monthly'

    def build(self):
        super(ActivityMonthlyReport, self).build()
        self.data['interval_label'] = 'month'


class ActivityYearlyReport(YearlyMixin, ActivityReport):
    "Yearly report"
    id = 'activity-year'
    label = 'Yearly'

    def build(self):
        super(ActivityYearlyReport, self).build()
        self.data['interval_label'] = 'year'


class ActivityQuarterlyReport(QuarterlyMixin, ActivityReport):
    "Quarterly report"
    id = 'activity-quarter'
    label = 'Quarterly'

    def build(self):
        super(ActivityQuarterlyReport, self).build()
        self.data['interval_label'] = 'quarter'

        if self.previous_date_start.year != self.date_start.year:
            self.data['period_labels'] = "%dQ%d" % (self.previous_date_start.year, date_to_quarter(self.previous_date_start)), "%dQ%d" % (self.date_start.year, date_to_quarter(self.date_start))
        else:
            self.data['period_labels'] = "Q%d" % date_to_quarter(self.previous_date_start), "Q%d" % date_to_quarter(self.date_start)

    def get_preview(self):
        if len(self.tables['summary'].rows) < 2:
            return u''

        this_week, last_week = self.data['total_current'], self.data['total_last']
        delta = (this_week / float(last_week or 1.0)) - 1
        return u"Your site had {this_week} this {interval} ({delta} over last {interval}).".format(
            this_week=h.format_int(this_week, self.data['total_units']),
            delta=h.human_percent(delta, signed=True),
            interval=self.data.get('interval_label', 'quarter'),
        )

    def _get_interval_field(self):
        return 'bm:quarter'

    def _get_interval_table(self, google_query, interval_field, params, dimensions=None, metrics=None, _cache_keys=None):
        if interval_field != 'bm:quarter':
            return google_query.get_table(params=params, dimensions=dimensions, metrics=metrics, _cache_keys=_cache_keys)

        dimensions += [Column('ga:year')]
        columns = google_query._columns_to_params(params.copy(), dimensions=dimensions, metrics=metrics)
        result = Table(columns).new() # Decouple column refs
        quarter_idx = result.column_to_index['bm:quarter']

        if dimensions:
            dimensions = [d for d in dimensions if not d.id.startswith('bm:quarter')]

        # We assume that there are no date dimensions... Maybe not a safe assumption?
        for (yr, q) in reversed(list(iter_quarters(params['start-date'], params['end-date']))):
            start_date, end_date = quarter_to_dates(q, yr)
            quarter_params = params.copy()
            quarter_params.update({
                'start-date': start_date,
                'end-date': end_date,
            })
            quarter_params.pop('sort', None)
            print(quarter_params)
            t = google_query.get_table(params=quarter_params, dimensions=dimensions, metrics=metrics, renew=True, _cache_keys=_cache_keys)

            quarter_str = "{}Q{}".format(yr, q)
            for row in t.rows:
                vals = row.values
                vals.insert(quarter_idx, quarter_str)
                result.add(vals)

        return result
