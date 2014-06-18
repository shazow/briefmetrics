from collections import OrderedDict
import datetime

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

        self.base_url = self.report.remote_data.get('websiteUrl', '')

        self.since_time = since_time
        self.previous_date_start, self.date_start, self.date_end, self.date_next = self.get_date_range(since_time)
        self.previous_date_end = self.date_start - datetime.timedelta(days=1)

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
        previous_date_start = date_start - datetime.timedelta(days=1)

        return previous_date_start, date_start, date_end, date_next

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

    def get_preview(self):
        return u''

    def build(self):
        pass
