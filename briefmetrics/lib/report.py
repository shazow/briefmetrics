from itertools import groupby, izip
import datetime

from . import helpers as h
from .gcharts import encode_rows


class Column(object):
    def __init__(self, id, label=None, type_cast=None, average=None, threshold=0.2):
        self.id = id
        self.label = label
        self.type_cast = type_cast
        self._threshold = threshold
        self._average = average and float(average)

        self.min = average, None
        self.max = average, None

    def cast(self, value):
        return self.type_cast(value) if self.type_cast else value

    def is_interesting(self, value, row=None):
        if not self._average:
            return False

        delta = (self._average - value) / self._average
        if abs(delta) < self._threshold:
            return False

        min, _ = self.min
        if min > value:
            self.min = value, row

        max, _ = self.max
        if max < value:
            self.max = value, row

        return True


class Table(object):
    def __init__(self, columns):
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
            values.append(value)
            column.is_interesting(value, r)

        self.rows.append(r)

    def get(self, id):
        "Return the column"
        return self.columns[self.column_to_index[id]]


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


class Report(object):
    def __init__(self, report, date_start):
        self.data = {}
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

    def _set_row_tags(self, row, state):
        if not state:
            state.update({'bounce': row, 'time': row})

        sitetime, bounce = map(float, row[2:4])

        #if sitetime > self.min_sitetime:
        #    row[-1].append('sitetime')

        #if bounce > self.min_bounce:
        #    row[-1].append('bounce')

        if sitetime > float(state['time'][2]):
            state['time'] = row

        if bounce < float(state['bounce'][3]):
            state['bounce'] = row

    def _set_state_rows(self, state):
        row = state['bounce']
        if float(row[3]) < self.tag_threshold['bounce']:
            row[4].append(u'\u2605 Best Bounce Rate')

        row = state['time']
        if float(row[2]) > self.tag_threshold['time']:
            row[4].append(u'\u2605 Best Time on Site')

    def add_referrers(self, r):
        social_search = self.data.setdefault('social_search', [])
        data = self.data.setdefault('referrers', [])

        state = {}
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
            self._set_row_tags(row, state)
            data.append(row)

        self._set_state_rows(state)

    def add_social(self, r):
        data = self.data.setdefault('social_search', [])

        state = {}
        for row in r['rows']:
            label, value = row[:2]
            if label.startswith('('):
                continue

            row.append([]) # Tags
            self._set_row_tags(row, state)
            data.append(row)

        self._set_state_rows(state)

    def _cumulative_by_month(self, rows, month_idx=1, value_idx=2):
        max = 0
        sum = 0

        months = []
        for month_num, data in groupby(rows, lambda r: r[month_idx]):
            rows = []
            for row in data:
                rows.append(sum)
                sum += float(row[value_idx])

            rows.append(sum)
            max = max(max, sum)
            sum = 0

            months.append(rows)

        return months, max

    def add_historic(self, r):
        monthly_data, max = self._cumulative_by_month(r['rows'])
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max)
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[len(current_month)-1]

    def add_summary(self, r):
        self.data['summary'] = summary = r['rows']
        time_on_site, bounce = map(float, summary[0][2:4])
        self.tag_threshold = {
            'bounce': bounce * 0.80,
            'time': time_on_site * 1.25,
        }

    def add_pages(self, r):
        data = self.data.setdefault('pages', [])

        state = {}
        for row in r['rows']:
            row.append([]) # Tags
            self._set_row_tags(row, state)
            data.append(row)

        self._set_state_rows(state)
