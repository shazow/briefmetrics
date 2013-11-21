from itertools import izip
from collections import OrderedDict
import datetime

from .gcharts import encode_rows


class Column(object):
    def __init__(self, id, label=None, type_cast=None, visible=None, average=None, threshold=None):
        self.table = None
        self.id = id
        self.label = label or id
        self.type_cast = type_cast
        self.visible = visible

        self._threshold = threshold
        self._average = average and float(average)

        if threshold is None and average is not None:
            self._threshold = 0.2

        self.min_row = average, None
        self.max_row = average, None
        self.sum = 0

    @property
    def average(self):
        return self.sum / float(len(self.table.rows) or 1)

    def new(self, visible=None):
        return Column(self.id, label=self.label, type_cast=self.type_cast, visible=visible, average=self.average)

    def cast(self, value):
        return self.type_cast(value) if self.type_cast else value

    def is_interesting(self, value, row=None):
        if self._threshold is None:
            return False

        self.sum += value

        min_value, _ = self.min_row
        if min_value > value:
            self.min_row = value, row

        max_value, _ = self.max_row
        if max_value < value:
            self.max_row = value, row

        if self._average is not None:
            delta = (self._average - value) / (self._average or 1)
            if abs(delta) < self._threshold:
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
    def __init__(self, column, value):
        self.column = column
        self.value = value


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
        for column in self.columns:
            if column.visible is not None:
                # We only want non-visible columns
                continue

            value, row = column.min_row
            if row:
                row.tags.append(RowTag(column=column, value=value))

            value, row = column.max_row
            if row:
                row.tags.append(RowTag(column=column, value=value))

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

    def build(self):
        monthly_data, max_value = self._cumulative_by_month(self.tables['historic'])
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[len(current_month)-1]

        t = Table(columns=[
            Column('source', label='Social & Search', visible=1),
            Column('ga:pageviews', label='Views', type_cast=int, visible=0, threshold=0),
            Column('ga:timeOnSite', type_cast=float, threshold=0),
            Column('ga:visitBounceRate', type_cast=float, threshold=0),
        ])

        for source, pageviews, tos, bounce in self.tables['social'].iter_rows():
            t.add([source, pageviews, tos, bounce])

        for source, pageviews, tos, bounce in self.tables['organic'].iter_rows():
            t.add([source.title(), pageviews, tos, bounce])

        t.sort(reverse=True)
        #t.rows = t.rows[:10]
        self.tables['social_search'] = t

        self.tables['social_search'].tag_rows()
        self.tables['referrers'].tag_rows()
        self.tables['pages'].tag_rows()
