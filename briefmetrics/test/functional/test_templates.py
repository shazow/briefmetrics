import datetime

from briefmetrics.web.environment import get_renderer
from briefmetrics.lib.report import get_report
from briefmetrics.lib import helpers as h
from briefmetrics import test
from briefmetrics import model

from ..fixtures.api_google import profile_item_template


class TestReportWidgets(test.TestApp):
    def test_intro(self):
        t = get_renderer('email/report/widgets.mako').template
        render_intro = t.get_def('render_intro').render

        empty_report = model.Report(remote_data=profile_item_template.copy(), type='week')
        since_time = datetime.datetime(2014, 3, 29)

        r = get_report('week')(empty_report, since_time)
        context = {'h': h}

        week_interval = r.previous_date_start, r.date_start, r.date_end
        month_interval = datetime.datetime(2013, 12, 1), datetime.datetime(2014, 1, 1), datetime.datetime(2014, 1, 31)
        year_interval = datetime.datetime(2013, 1, 1), datetime.datetime(2014, 1, 1), datetime.datetime(2014, 1, 31)

        data = [
            # current, last, last_relative, week_interval, expected
            (123, 234, 42, week_interval,
                u"Your site had 123 views so far this month, compared to last month's 42 views at this time. You're on your way to beat last month's total of 234.",
            ),
            (300, 234, 42, week_interval,
                u"Your site had 300 views so far this month, compared to last month's 42 views at this time. You're already ahead of last month's total of 234!",
            ),
            (20, 234, 42, week_interval,
                u"Your site had 20 views so far this month, compared to last month's 42 views at this time and 234 by the end of last month.",
            ),
            (123, 234, 42, month_interval,
                u"Your site had 123 views in January, compared to December's total of 234.",
            ),
            (20, 234, 42, month_interval,
                u"Your site had 20 views in January, compared to December's total of 234.",
            ),
            (20, 234, 234, week_interval,
                u"Your site had 20 views so far this month, compared to last month's 234 views at this time and 234 by the end of last month.",
            ),
            (30, 334, 42, year_interval,
                u"Your site had 30 views in January 2014, compared to January 2013's total of 334.",
            ),
        ]

        for current, last, last_relative, interval, _expected in data:
            s = render_intro(
                current=current,
                last=last,
                last_relative=last_relative,
                units=u'{:,} view',
                interval=interval,
                **context
            )

            self.assertEqual(
                h.html_to_text(s, strip_spaces=True),
                _expected,
            )
