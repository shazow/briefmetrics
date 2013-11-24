from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics import tasks
from briefmetrics.lib.report import Report, WeeklyReport, Column, Table
from briefmetrics.lib.controller import Context

from briefmetrics.test.fixtures.api_google import FakeQuery

import mock
import datetime

Session = model.Session


@mock.patch('briefmetrics.api.google.Query', FakeQuery)
class TestReport(test.TestWeb):
    def _create_report(self):
        remote_data = FakeQuery().get_profiles(1)['items'][0]
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        report = model.Report.create(account=u.account, remote_data=remote_data, display_name=u'example.com')
        model.Subscription.create(user=u, report=report)
        Session.commit()
        return report

    def test_fake_query(self):
        q = FakeQuery(None)
        r = q.get_profiles(1)
        self.assertEqual(r[u'username'], u'example@example.com')

        q = api.google.Query(None)
        r = q.get_profiles(1)
        self.assertEqual(r[u'username'], u'example@example.com')

        t = q.get_table({'max-results': 5}, dimensions=[
            Column('ga:pagePath'),
        ], metrics=[
            Column('ga:pageviews', type_cast=int, threshold=0),
            Column('ga:week'),
        ])
        self.assertEqual(len(t.rows), 5)
        self.assertEqual(t.rows[1].get('ga:pagePath'), '/bar')
        self.assertEqual(t.rows[1].get('ga:pageviews'), 123)
        self.assertEqual(t.get('ga:pageviews').max_row[0], 1234567)

        t = q.get_table({'max-results': 7}, dimensions=[Column('ga:month')])
        self.assertEqual([list(m) for m in t.iter_rows()], [[1], [1], [1], [1], [1], [1], [2]]) 

    def test_fetch_weekly(self):
        report = self._create_report()

        context = api.report.fetch_weekly(self.request, report, datetime.date(2013, 1, 6))
        self.assertEqual(context.date_end, datetime.date(2013, 1, 12))
        self.assertEqual(context.date_next, datetime.date(2013, 1, 21))
        self.assertEqual(context.get_subject(), u'Report for example.com (Jan 6-12)')

        html = api.report.render(self.request, 'email/report.mako', Context({
            'report': context,
            'user': context.owner,
        }))
        self.assertTrue(html)

    def test_empty(self):
        report = self._create_report()
        google_query = FakeQuery(_num_rows=0)
        context = api.report.fetch_weekly(self.request, report, datetime.date(2013, 1, 6), google_query=google_query)
        self.assertFalse(context.data)

        # TODO: Test send_weekly.
        html = api.report.render(self.request, 'email/error_empty.mako', Context({
            'report': context,
            'user': context.owner,
        }))
        self.assertIn('no results for your site', html)


    def test_send_weekly(self):
        report = self._create_report()
        self.assertEqual(report.time_next, None)
        self.assertEqual(model.Report.count(), 1)

        user = report.account.user
        user.num_remaining = 1
        model.Session.commit()

        tasks.report.celery.request = self.request

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)

        self.assertEqual(model.Report.count(), 1)

        Session.refresh(report)
        self.assertNotEqual(report.time_next, None)
        self.assertEqual(report.account.user.num_remaining, 0)

        # Send all too early
        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertFalse(send_message.called)

        self.assertEqual(model.Report.count(), 1)

        Session.refresh(report)
        self.assertEqual(report.account.user.num_remaining, 0)

        # Reset time and send again
        report.time_next = None
        model.Session.commit()

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)

            call, = send_message.call_args_list
            message = call[0][1]
            self.assertEqual(message['subject'], u"Your Briefmetrics trial is over")

        # Report should be deleted.
        self.assertEqual(model.Report.count(), 0)
        self.assertEqual(model.ReportLog.count(), 1)

        model.Session.refresh(user)
        self.assertEqual(user.num_remaining, 0)

    def test_api(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        r = self.call_api('report.create', remote_id=u'111112')
        report = r['result']['report']
        self.assertEqual(report['display_name'], u'example.com')
        self.assertEqual(model.Report.count(), 1)

        r = self.call_api('report.update', report_id=report['id'], delete=u'true')
        self.assertEqual(model.Report.count(), 0)


class TestReportModel(test.TestCase):

    def test_encode_preferred(self):
        self.assertEqual(model.Report.encode_preferred_time(), datetime.datetime(1900, 1, 1, 13, 0, 0)) # Default
        self.assertEqual(model.Report.encode_preferred_time(hour=8, minute=15), datetime.datetime(1900, 1, 1, 8, 15, 0))
        self.assertEqual(model.Report.encode_preferred_time(hour=0, minute=0, second=0), datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(model.Report.encode_preferred_time(weekday=0).date(), datetime.date(1900, 1, 8)) # Monday
        self.assertEqual(model.Report.encode_preferred_time(weekday=6).date(), datetime.date(1900, 1, 14)) # Sunday

    def test_next_preferred(self):
        now = datetime.datetime(2013, 1, 1, 7, 35, 15) # Tuesday

        r = model.Report(type='day')

        r.set_time_preferred(hour=12)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 2, 12, 0, 0))

        r = model.Report(type='week')
        # Default to Monday @ 8pm EST for weekly
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 7, 13, 0, 0))
        self.assertEqual(r.next_preferred(datetime.date(2013, 1, 12)), datetime.datetime(2013, 1, 14, 13)) # Sat -> Mon

        # Wednesdays @ 12pm UTC
        r.set_time_preferred(weekday=2, hour=12)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 2, 12, 0, 0))

        # Mondays @ 12pm UTC
        r.set_time_preferred(weekday=0, hour=12)
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 1, 7, 12, 0, 0))


class TestReportLib(test.TestCase):
    def _create_report_model(self, type='day'):
        return model.Report(
            remote_id=1,
            remote_data={},
            display_name='example.com',
            type=type,
        )

    def test_base(self):
        report = self._create_report_model('day')
        date_start = datetime.date(2013, 1, 1)

        r = Report(report, date_start)

        self.assertEqual(r.date_end, datetime.date(2013, 1, 1))
        self.assertEqual(r.date_next, datetime.date(2013, 1, 2))
        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 1)")

    def test_weekly(self):
        report = self._create_report_model('week')
        date_start = datetime.date(2013, 1, 6) # First Sunday
        r = WeeklyReport(report, date_start)

        self.assertEqual(r.date_end, datetime.date(2013, 1, 12)) # Next Saturday
        self.assertEqual(r.date_next, datetime.date(2013, 1, 21)) # Week from Monday

        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 6-12)")

        date_start = datetime.date(2013, 1, 27) # Last Sunday
        r = WeeklyReport(report, date_start)

        self.assertEqual(r.date_end, datetime.date(2013, 2, 2)) # Next Saturday
        self.assertEqual(r.date_next, datetime.date(2013, 2, 11)) # Week from Monday

        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 27-Feb 2)")

    def test_table_column(self):
        s = Column('foo', type_cast=int)
        self.assertEqual(s.cast('123'), 123)
        self.assertEqual(s.min_row, (None, None))
        self.assertEqual(s.max_row, (None, None))

        s = Column('foo', average=100, threshold=0.25)
        self.assertEqual(s.min_row, (100.0, None))
        self.assertEqual(s.max_row, (100.0, None))

        self.assertFalse(s.is_interesting(90, 'a'))
        self.assertEqual(s.min_row, (90.0, 'a'))
        self.assertEqual(s.max_row, (100.0, None))

        self.assertTrue(s.is_interesting(50, 'b'))
        self.assertEqual(s.min_row, (50.0, 'b'))
        self.assertEqual(s.max_row, (100.0, None))

        self.assertTrue(s.is_interesting(150, 'c'))
        self.assertEqual(s.min_row, (50.0, 'b'))
        self.assertEqual(s.max_row, (150.0, 'c'))

        self.assertTrue(s.is_interesting(200, 'd'))
        self.assertEqual(s.min_row, (50.0, 'b'))
        self.assertEqual(s.max_row, (200.0, 'd'))

    def test_table_rows(self):
        t = Table([
            Column('foo'),
            Column('bar'),
            Column('baz', type_cast=int, average=100),
        ])

        data = [
            (9999, '1', 123),
            (0123, '2', 1234),
            (0000, '3', 23),
            (0123, '4', 123),
        ]

        for d in data:
            t.add(d)

        self.assertEqual(len(t.rows), 4)
        self.assertEqual(t.get('foo').min_row, (None, None))
        self.assertEqual(t.get('bar').max_row, (None, None))
        self.assertEqual(t.get('baz').min_row[0], 23)
        self.assertEqual(t.get('baz').max_row[0], 1234)
