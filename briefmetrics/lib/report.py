from itertools import groupby, izip
import datetime

from . import helpers as h
from .gcharts import encode_rows


class Column(object):
    def __init__(self, id, label=None, type_cast=None, visible=None, average=None, threshold=0.2):
        self.id = id
        self.label = label or id
        self.type_cast = type_cast
        self.visible = visible
        self._threshold = threshold
        self._average = average and float(average)

        self.min_row = average, None
        self.max_row = average, None
        self.sum = 0

    def cast(self, value):
        return self.type_cast(value) if self.type_cast else value

    def is_interesting(self, value, row=None):
        if not self._average:
            return False

        self.sum += value

        delta = (self._average - value) / self._average
        if abs(delta) < self._threshold:
            return False

        min_value, _ = self.min_row
        if min_value > value:
            self.min_row = value, row

        max_value, _ = self.max_row
        if max_value < value:
            self.max_row = value, row

        return True


class Row(object):
    __slots__ = [
        'values',
        'table',
        'tags',
    ]

    def __init__(self, table, values):
        self.table = table
        self.values = values
        self.tags = []

    def get(self, id):
        return self.values[self.table.column_to_index[id]]


class Table(object):
    def __init__(self, columns):
        # Columns must be in the same order as the rows that get added.
        self.columns = columns
        self.rows = []
        self.column_to_index = {s.id: i for i, s in enumerate(columns)}

    def add(self, row):
        values = []
        r = Row(self, values)
        for column, value in izip(self.columns, row):
            if not column:
                continue

            value = column.cast(value)
            if not value and column.visible is not None:
                # Skip row
                return

            values.append(value)
            column.is_interesting(value, r)

        self.rows.append(r)

    def get(self, id):
        "Return the column"
        return self.columns[self.column_to_index[id]]

    def get_visible(self):
        visible_columns = (c for c in self.columns if c.visible is not None)
        return sorted(visible_columns, key=lambda o: o.visible)

    def iter_rows(self, *column_ids):
        column_positions = [self.column_to_index[id] for id in column_ids]
        for row in self.rows:
            yield (row.values[i] for i in column_positions)

    def iter_visible(self, max_columns=None):
        ordered_columns = self.get_visible()[:max_columns]
        column_positions = [self.column_to_index[c.id] for c in ordered_columns]
        yield ordered_columns

        for row in self.rows:
            yield (row.values[i] for i in column_positions)


class Report(object):
    def __init__(self, report, date_start):
        self.data = {}
        self.tables = {}
        self.report = report
        self.owner = report.account and report.account.user
        self.remote_id = report.remote_id

        if not self.remote_id:
            # TODO: Remove this after backfill
            self.remote_id = report.remote_id = report.remote_data['id']

        self.base_url = self.report.remote_data.get('websiteUrl', '')

        self.date_start = date_start
        self._set_date_range()

    @classmethod
    def create_from_now(cls, report, now):
        # TODO: Take into account preferred time.
        date_start = now.date()
        return cls(report, date_start)

    def _set_date_range(self):
        self.date_end = self.date_start
        self.date_next = self.report.next_preferred(self.date_end).date()

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


class WeeklyReport(Report):
    REFERRERS_REDUNDANT = set([
        u'disqus.com',
        u'facebook.com',
        u'getpocket.com',
        u'linkedin',
        u'm.facebook.com',
        u'netvibes.com',
        u't.co',
        u'twitter',
    ])

    REFERRERS_SEARCH = set([
        u'aol',
        u'ask',
        u'bing',
        u'buffer',
        u'feedburner',
        u'google',
        u'hackernewsletter',
        u'medium',
        u'pulsenews',
        u'smallhq',
        u'yahoo',
    ])
    # TODO: Support arbitrary tlds for major domains? (google.ca etc)

    def _set_date_range(self):
        self.date_end = self.date_start + datetime.timedelta(days=6)
        self.date_next = self.report.next_preferred(self.date_end + datetime.timedelta(days=7)).date()

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

    def add_referrers(self, r):
        social_search = self.tables.setdefault('social_search', [])
        data = self.data.setdefault('referrers', [])

        for row in r['rows']:
            label, value = row[:2]
            if label.startswith('('):
                continue

            domain = h.human_url(label).split('/', 1)[0]

            if domain in self.REFERRERS_REDUNDANT:
                continue

            if domain in self.REFERRERS_SEARCH:
                social_search.append([domain.title(), value])
                continue

            row.append([]) # Tags
            data.append(row)

    def _cumulative_by_month(self, table):
        sum = 0

        months = []
        for _, rows in groupby(table.rows, lambda r: r.get('ga:month')):
            rows = []
            for row in rows:
                rows.append(sum)
                sum += float(row.get('ga:pageviews'))

            rows.append(sum)
            sum = 0

            months.append(rows)

        return months

    def build(self):
        max_value, _ = self.tables['historic'].get('ga:pageviews').max_row
        monthly_data = self._cumulative_by_month(self.tables['historic'])
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[len(current_month)-1]
