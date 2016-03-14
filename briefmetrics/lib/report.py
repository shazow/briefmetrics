from collections import OrderedDict
import datetime
import calendar

from briefmetrics.lib import helpers as h
from briefmetrics.lib.table import Column
from briefmetrics.lib.registry import registry_metaclass


def cumulative_by_month(month_views_iter):
    months = OrderedDict()
    max_value = 0
    for month, views in month_views_iter:
        month_list = months.get(month)
        if not month_list:
            month_list = months[month] = [0]
            last_val = 0
        else:
            last_val = month_list[-1]
        val = last_val + views
        month_list.append(val)
        max_value = max(max_value, val)

    return months.values(), max_value


def days_in_month(dt):
    _, days = calendar.monthrange(dt.year, dt.month)
    return days


def sparse_cumulative(iterable, final_date=None):
    "Data must be ascending."
    cumulated = OrderedDict()

    max_value = data = key = last_dt = last_amount = 0

    for dt, amount in iterable:
        if dt.month != key:
            if data:
                # Wrap up thelast month
                data += [last_amount] * (days_in_month(last_dt) - last_dt.day)
                max_value = max(last_amount, max_value)
                last_dt = last_amount = 0

            key = dt.month
            cumulated[key] = data = []

        # Backfill missing days
        if last_dt and last_dt.day < dt.day:
            data += [last_amount] * (dt.day - last_dt.day)

        last_dt = dt
        last_amount += amount

    if final_date:
        if final_date.month == last_dt.month:
            data += [last_amount] * (final_date.day - last_dt.day + 1)
        else:
            data += [last_amount] * (days_in_month(last_dt) - last_dt.day)
            cumulated[final_date.month] = [0] * final_date.day
    else:
        data.append(last_amount)

    return cumulated.values(), max(last_amount, max_value)


# TODO: Move this into lib/table.py
def split_table_delta(t, split_column, join_column, compare_column):
    """
    Split rows in table `t` between different `split_column` values.

    Must be sorted by `split_column`.
    """
    if not t.rows:
        return

    idx_split = t.column_to_index[split_column]
    idx_join = t.column_to_index[join_column]
    idx_compare = t.column_to_index[compare_column]
    col_compare = t.get(compare_column)

    split_val = t.rows[0].values[idx_split]
    num = next((i for i, row in enumerate(t.rows) if row.values[idx_split] != split_val), None)
    if num is None:
        return

    last_rows = t.rows[num:]
    last_lookup = dict((row.values[idx_join], row) for row in last_rows)
    t.rows = t.rows[:num]  # Truncate split rows

    for row in t.rows:
        cmp = row.values[idx_join]
        last_row = last_lookup.get(cmp)
        if not last_row:
            continue

        val = row.values[idx_compare]
        last_val = last_row.values[idx_compare]
        delta = val-last_val
        if not delta or abs(delta) < col_compare._threshold:
            continue

        row.tag(type=col_compare.label, value=delta)


# TODO: Move this into lib/table.py
def inject_table_delta(a, b, join_column, compare_column='ga:pageviews', num_normal=10, num_missing=5):
    """
    Annotate rows in table `a` with deltas from table `b`.

    Also add `num_missing` top rows from `b` that are not present in `a`.

    It's basically a left-join with extra sauce.
    """
    col_compare = a.get(compare_column)
    a_lookup = set(source for source, in a.iter_rows(join_column))
    b_lookup = dict((source, views) for source, views in b.iter_rows(join_column, compare_column))

    # Annotate delta tags
    col_compare_delta = Column('%s:delta' % col_compare.id, label=col_compare.label, type_cast=float, type_format=h.human_delta, threshold=0)
    idx_join, idx_compare = a.column_to_index[join_column], a.column_to_index[compare_column]
    for row in a.rows:
        j, views = row.values[idx_join], row.values[idx_compare]
        last_views = b_lookup.get(j) or 0
        views_delta = (views - last_views) / float(views)

        if not last_views:
            row.tag(type='new')
        elif abs(views_delta) > 0.20:
            row.tag(type='delta', value=views_delta, column=col_compare_delta)

    a.limit(num_normal)

    # Add missing entries
    for source, views in b.iter_rows(join_column, compare_column):
        if source in a_lookup:
            continue

        if col_compare.is_boring(views):
            break # Done early

        row = a.add([source, 0, 0, None, None, -views], is_measured=False)
        row.tag(type='views', value=h.human_int(-views), is_positive=False, is_prefixed=True)

        num_missing -= 1
        if num_missing <= 0:
            break


class EmptyReportError(Exception):
    pass


##

registry = {}

def get_report(id):
    return registry[id]

#

class Report(object):
    __metaclass__ = registry_metaclass(registry)

    id = None
    label = ''
    template = 'email/report/daily.mako'
    frequency = 'day'

    def __init__(self, report, since_time, config=None):
        self.data = {}
        self.tables = {}
        self.report = report
        self.owner = report.account and report.account.user
        self.remote_id = report.remote_id
        self.messages = []
        self.config = {}
        if self.owner:
            self.config.update(self.owner.config)
        if report.config:
            self.config.update(report.config)
        if config:
            self.config.update(config)

        self.include_permalinks = self.config.get('include_permalinks', True)

        self.since_time = since_time
        self.previous_date_start, self.date_start, self.date_end, self.date_next = self.get_date_range(since_time)
        self.previous_date_end = self.date_start - datetime.timedelta(days=1)

    @classmethod
    def create_from_now(cls, report, now):
        # TODO: Take into account preferred time.
        date_start = now.date()
        return cls(report, date_start)

    def get_query_params(self):
        return {
            'id': self.remote_id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }

    def get_preview(self):
        return u''

    def build(self):
        pass

    def next_preferred(self, now):
        # TODO: Use combine?
        # TODO: Use delorean/arrow? :/
        time_preferred = self.report.time_preferred or self.report.encode_preferred_time()
        datetime_tuple = now.timetuple()[:3] + time_preferred.timetuple()[3:6]
        now = datetime.datetime(*datetime_tuple)
        days_offset = 0

        # TODO: Break it out into separate member methods per mixin?
        if self.frequency == 'day':
            days_offset = 1

        elif self.frequency == 'week':
            preferred_weekday = time_preferred.weekday() if time_preferred.day > 1 else 0
            days_offset = preferred_weekday - now.weekday()
            if days_offset < 0:
                days_offset += 7

        elif self.frequency == 'month':
            next_month = now.replace(day=1) + datetime.timedelta(days=32)
            next_month = next_month.replace(day=1)

            if time_preferred.day != 1:
                weekday_offset = time_preferred.weekday() - next_month.weekday()
                if weekday_offset:
                    next_month += datetime.timedelta(days=7 + weekday_offset)

            days_offset = (next_month - now).days

        elif self.frequency == 'year':
            next_year = now.replace(day=1, month=1, year=now.year+1)
            if time_preferred.day != 1:
                weekday_offset = time_preferred.weekday() - next_month.weekday()
                if weekday_offset:
                    next_month += datetime.timedelta(days=7 + weekday_offset)
            days_offset = (next_year - now).days

        else:
            raise ValueError('Invalid type: %s' % self.frequency)

        return now + datetime.timedelta(days=days_offset)



class DailyMixin(object):
    frequency = 'day'

    def get_date_range(self, since_time):
        """
        Returns a (start, end, next) date tuple.
        """
        date_start = (since_time - datetime.timedelta(days=1)).date()
        date_end = date_start
        date_next = self.next_preferred(date_end).date()
        previous_date_start = date_start - datetime.timedelta(days=1)

        return previous_date_start, date_start, date_end, date_next

    def get_subject(self):
        return u"Report for {site} ({date})".format(
            date=self.date_start.strftime('%b {}').format(self.date_start.day),
            site=self.report.display_name,
        )


class MonthlyMixin(object):
    frequency = 'month'

    def get_date_range(self, since_time):
        since_start = since_time.date().replace(day=1) 
        date_end = since_start - datetime.timedelta(days=1) # Last of the previous month
        date_start = date_end.replace(day=1) # First of the previous month
        date_next = self.next_preferred(since_start).date()
        previous_date_start = (date_start - datetime.timedelta(days=1)).replace(day=1)

        return previous_date_start, date_start, date_end, date_next

    def get_subject(self):
        return u"Report for {site} ({date})".format(
            date=self.date_start.strftime('%B'),
            site=self.report.display_name,
        )


class YearlyMixin(object):
    frequency = 'year'

    def get_date_range(self, since_time):
        since_start = since_time.date().replace(day=1, month=1)
        date_start = since_start.replace(year=since_time.year-1)
        date_end = since_start - datetime.timedelta(days=1) # Last day of the previous year
        date_next = self.next_preferred(since_start).date()
        previous_date_start = (date_start - datetime.timedelta(days=1)).replace(day=1, month=1)

        return previous_date_start, date_start, date_end, date_next

    def get_subject(self):
        return u"Report for {site} ({date})".format(
            date=self.date_start.strftime('%Y'),
            site=self.report.display_name,
        )


class WeeklyMixin(object):
    frequency = 'week'

    def get_date_range(self, since_time):
        # Last Sunday
        date_start = since_time.date() - datetime.timedelta(days=6) # Last week
        date_start -= datetime.timedelta(days=date_start.weekday()+1) # Sunday of that week
        date_end = date_start + datetime.timedelta(days=6)
        date_next = self.next_preferred(date_end + datetime.timedelta(days=7)).date()
        previous_date_start = date_start - datetime.timedelta(days=7) # +1 day to account for the no-overlap.

        return previous_date_start, date_start, date_end, date_next

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
