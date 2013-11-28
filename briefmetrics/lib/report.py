from itertools import izip
from collections import OrderedDict
import datetime

from .gcharts import encode_rows
from . import helpers as h


def _prune_abstract(label):
    if label.startswith('('):
        return
    return label


class Column(object):
    def __init__(self, id, label=None, type_cast=None, type_format=None, visible=None, reverse=False, average=None, threshold=None):
        self.table = None
        self.id = id
        self.label = label or id
        self.type_cast = type_cast
        self.type_format = type_format
        self.visible = visible
        self.reverse = reverse

        self._threshold = threshold
        self._average = average and float(average)

        if threshold is None and average is not None:
            self._threshold = 0.2

        self.min_row = average, None
        self.max_row = average, None
        self.sum = 0

    @property
    def average(self):
        if self._threshold is None:
            return
        return self.sum / float(len(self.table.rows) or 1)

    def new(self):
        return Column(self.id, label=self.label, type_cast=self.type_cast, type_format=self.type_format, visible=self.visible, reverse=self.reverse, average=self.average)

    def cast(self, value):
        return self.type_cast(value) if self.type_cast else value

    def format(self, value):
        return self.type_format(value) if self.type_format else value

    def delta_value(self, value):
        return self._average is not None and (self._average - value) / (self._average or 1)

    def is_interesting(self, value, row=None):
        if value is None or self._threshold is None:
            return False

        self.sum += value

        min_value, _ = self.min_row
        if min_value > value:
            self.min_row = value, row

        max_value, _ = self.max_row
        if max_value < value:
            self.max_row = value, row

        delta = self.delta_value(value)
        if delta and abs(delta) < self._threshold:
            return False

        return True

    def is_boring(self, value, threshold=0.005):
        if value is None:
            return True

        max_value, _ = self.max_row
        if not max_value:
            return False

        return not value or value < max_value * threshold

    def __repr__(self):
        return '{class_name}(id={self.id!r})'.format(class_name=self.__class__.__name__, self=self)


class RowTag(object):
    def __init__(self, column, value, type=None):
        self.column = column
        self.value = value
        self.type = type

    @property
    def delta_value(self):
        return self.column.delta_value(self.value)

    @property
    def is_positive(self):
        return (self.type == 'max') != self.column.reverse

    def __str__(self):
        parts = []

        if self.type in ['min', 'max']:
            pos = int(self.is_positive)
            adjective = ['Worst', 'Best'][pos]
            parts.append(adjective)

        parts.append(self.column.label)
        return ' '.join(parts)


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

    def __repr__(self):
        return '{class_name}(values={self.values!r})'.format(class_name=self.__class__.__name__, self=self)


class Table(object):
    def __init__(self, columns):
        # Columns must be in the same order as the rows that get added.
        self.columns = columns
        self.rows = []
        self.column_to_index = {s.id: i for i, s in enumerate(columns)}

        for column in columns:
            column.table = self

    def add(self, row):
        values = []
        r = Row(self, values)
        for column, value in izip(self.columns, row):
            if not column:
                continue

            value = column.cast(value)
            if column.visible is not None and column.is_boring(value):
                # Skip row
                return

            values.append(value)
            column.is_interesting(value, r)

        self.rows.append(r)

    def sort(self, reverse=False):
        visible_columns = next(self.iter_visible())
        column_pos = sorted((col.visible, self.column_to_index[col.id]) for col in visible_columns if col.visible is not None)
        self.rows.sort(key=lambda r: [r.values[pos] for _, pos in column_pos], reverse=reverse)

    def get(self, id):
        "Return the column"
        return self.columns[self.column_to_index[id]]

    def get_visible(self):
        visible_columns = (c for c in self.columns if c.visible is not None)
        return sorted(visible_columns, key=lambda o: o.visible)

    def tag_rows(self):
        if len(self.rows) < 3:
            return

        for column in self.columns:
            if column.visible is not None or column._threshold is None:
                # We only want non-visible thresholded columns
                continue

            value, row = column.max_row
            if row:
                row.tags.append(RowTag(column=column, value=value, type='max'))

            value, row = column.min_row
            if row:
                row.tags.append(RowTag(column=column, value=value, type='min'))


    def iter_rows(self, *column_ids):
        if not column_ids:
            column_ids = [col.id for col in self.columns]

        column_positions = [self.column_to_index[id] for id in column_ids]
        for row in self.rows:
            yield (row.values[i] for i in column_positions)

    def iter_visible(self, max_columns=None):
        ordered_columns = self.get_visible()[:max_columns]
        column_positions = [self.column_to_index[c.id] for c in ordered_columns]
        yield ordered_columns

        for row in self.rows:
            yield (row.values[i] for i in column_positions)



class EmptyReportError(Exception):
    pass


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

    def build(self):
        pass


class WeeklyReport(Report):
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

    def _cumulative_by_month(self, table):
        months = OrderedDict()
        max_value = 0
        for month, pageviews in table.iter_rows('ga:month', 'ga:pageviews'):
            month_list = months.get(month)
            if not month_list:
                month_list = months[month] = []
                last_val = 0
            else:
                last_val = month_list[-1]
            val = last_val + pageviews
            month_list.append(val)
            max_value = max(max_value, val)

        return months.values(), max_value

    def fetch(self, google_query):
        # Summary
        summary_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:uniquePageviews', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgTimeOnSite', label='Time On Site', type_cast=lambda v: float(v) or None, type_format=h.human_time, threshold=0),
            Column('ga:visitBounceRate', label='Bounce Rate', type_cast=lambda v: float(v) / 100.0 or None, type_format=h.human_percent, reverse=True, threshold=0),
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
            metrics=summary_metrics,
        )

        # Pages
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

        self.tables['historic'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start_last_month,
                'end-date': self.date_end,
            },
            dimensions=[
                Column('ga:date'),
                Column('ga:month'),
            ],
            metrics=[
                Column('ga:pageviews', type_cast=int),
            ],
        )
        monthly_data, max_value = self._cumulative_by_month(self.tables['historic'])
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
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
        #t.rows = t.rows[:10]
        self.tables['social_search'] = t

        self.tables['social_search'].tag_rows()
        self.tables['referrers'].tag_rows()
        self.tables['pages'].tag_rows()
