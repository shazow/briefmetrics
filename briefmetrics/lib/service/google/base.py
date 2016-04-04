import datetime
from briefmetrics.lib.table import Table, Column
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib import helpers as h
from briefmetrics.lib.report import (
    Report,
    MonthlyMixin,
    DailyMixin,
    cumulative_by_month,
)

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

# TODO: Rename ids to GA-specific

class GAReport(Report):
    def __init__(self, report, since_time, remote_data=None, display_name=None, config=None):
        super(GAReport, self).__init__(report, since_time, config=config)
        if remote_data:
            self.remote_id = str(remote_data.get('id', self.remote_id))

        self.remote_data = remote_data = remote_data or self.report.remote_data or {}
        self.display_name = display_name or report.display_name

        base_url = remote_data.get('websiteUrl', '')
        if base_url and 'http://' not in base_url:
            base_url = 'http://' + base_url

        self.base_url = remote_data.get('websiteUrl', '')
