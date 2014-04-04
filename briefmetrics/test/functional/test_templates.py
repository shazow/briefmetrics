import datetime

from briefmetrics.web.environment import get_renderer
from briefmetrics.lib.report import ActivityReport
from briefmetrics.lib import helpers as h
from briefmetrics import test
from briefmetrics import model

from ..fixtures.api_google import profile_item_template


class TestReportWidgets(test.TestApp):
    def test_intro(self):
        t = get_renderer('email/report/widgets.mako').implementation()
        render_intro = t.get_def('render_intro').render

        empty_report = model.Report(remote_data=profile_item_template.copy())
        since_time = datetime.datetime(2014, 3, 29)

        r = ActivityReport(empty_report, since_time)
        context = {'h': h}

        week_interval = r.date_start, r.date_end
        month_interval = datetime.datetime(2014, 1, 1), datetime.datetime(2014, 1, 31)

        data = [
            # current, last, last_relative, week_interval, expected
            (123, 234, 42, week_interval,
                u"Your site had 123 views so far this month, compared to last month's 42 views at this time. You're on your way to beat last months's total of 234.",
            ),
            (300, 234, 42, week_interval,
                u"Your site had 300 views so far this month, compared to last month's 42 views at this time. You're already ahead of last months's total of 234!",
            ),
            (20, 234, 42, week_interval,
                u"Your site had 20 views so far this month, compared to last month's 42 views at this time.",
            ),
            (123, 234, 42, month_interval,
                u"Your site had 123 views this month, compared to last months's total of 234.",
            ),
            (20, 234, 42, month_interval,
                u"Your site had 20 views this month, compared to last months's total of 234.",
            ),
            (20, 234, 234, week_interval,
                u"Your site had 20 views so far this month, compared to last month's 234 views at this time.",
            ),
        ]

        for current, last, last_relative, current_interval, _expected in data:
            s = render_intro(
                current=current,
                last=last,
                last_relative=last_relative,
                units=u'{:,} view',
                current_interval=current_interval,
                **context
            )

            self.assertEqual(
                h.html_to_text(s, strip_spaces=True),
                _expected,
            )
