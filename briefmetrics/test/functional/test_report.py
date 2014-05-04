from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics import tasks
from briefmetrics.lib.report import Report, get_report, month_date_range
from briefmetrics.lib.table import Column
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
            Column('ga:nthWeek'),
        ])
        self.assertEqual(len(t.rows), 5)
        self.assertEqual(t.rows[1].get('ga:pagePath'), '/bar')
        self.assertEqual(t.rows[1].get('ga:pageviews'), 1001)
        self.assertEqual(t.get('ga:pageviews').max_row[0], 1999)

        t = q.get_table({'max-results': 7}, dimensions=[Column('ga:month')])
        self.assertEqual([list(m) for m in t.iter_rows()], [[1]]*6 + [[2]]) 

    def test_fetch(self):
        report = self._create_report()

        since_time = datetime.datetime(2013, 1, 13)
        context = api.report.fetch(self.request, report, since_time)
        self.assertEqual(context.date_end, datetime.date(2013, 1, 12))
        self.assertEqual(context.date_next, datetime.date(2013, 1, 21))
        self.assertEqual(context.get_subject(), u'Report for example.com (Jan 6-12)')

        html = api.report.render(self.request, context.template, Context({
            'report': context,
            'user': context.owner,
        }))
        self.assertTrue(html)

    def test_empty(self):
        report = self._create_report()
        google_query = FakeQuery(_num_rows=0)
        since_time = datetime.datetime(2013, 1, 13)
        context = api.report.fetch(self.request, report, since_time, google_query=google_query)
        self.assertFalse(context.data)

        # TODO: Test send.
        html = api.report.render(self.request, 'email/error_empty.mako', Context({
            'report': context,
            'user': context.owner,
        }))
        self.assertIn('no results for your site', html)


    def test_send(self):
        report = self._create_report()
        self.assertEqual(report.time_next, None)
        self.assertEqual(model.Report.count(), 1)

        user = report.account.user
        user.num_remaining = 1
        Session.commit()

        tasks.report.celery.request = self.request

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)

        self.assertEqual(model.Report.count(), 1)

        Session.refresh(report)
        self.assertNotEqual(report.time_next, None)
        self.assertEqual(report.account.user.num_remaining, 0)

        # Send all again, should skip because too early
        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertFalse(send_message.called)

        self.assertEqual(model.Report.count(), 1)

        Session.refresh(report)
        self.assertEqual(report.account.user.num_remaining, 0)

        # Reset time and send again
        report.time_next = None
        Session.commit()

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            tasks.report.send_all(async=False)
            self.assertTrue(send_message.called)

            call, = send_message.call_args_list
            message = call[0][1]
            self.assertEqual(message['subject'], u"Your Briefmetrics trial is over")

        # Report should be deleted.
        self.assertEqual(model.Report.count(), 0)
        self.assertEqual(model.ReportLog.count(), 1)

        Session.refresh(user)
        self.assertEqual(user.num_remaining, 0)

    def test_api(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        r = self.app.get('/reports')
        self.assertIn('New report', r)
        self.assertNotIn('Active reports', r)

        r = self.call_api('report.create', remote_id=u'200001')
        report = r['result']['report']
        self.assertEqual(report['display_name'], u'example.com')
        self.assertEqual(model.Report.count(), 1)

        r = self.app.get('/reports')
        self.assertIn('Active reports', r)

        r = self.call_api('report.delete', report_id=report['id'])
        self.assertEqual(model.Report.count(), 0)

    def test_limits(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        # Limit number of sites & recipients
        u.config['num_recipients'] = 1
        u.config['num_sites'] = 1
        Session.commit()

        r = self.call_api('report.create', remote_id=u'200001', type='week')
        report_id = r['result']['report']['id']

        # Same site twice is cool
        r = self.call_api('report.create', remote_id=u'200001', type='month')

        # Different site exceeds site limit
        r = self.call_api('report.create', _status=400, remote_id=u'200002')

        # Adding a subscriber to the first report also exceeds
        r = self.call_api('subscription.create', _status=400, report_id=report_id, email='foo@example.com', display_name='Foo')

        self.assertEqual(model.User.count(), 1)
        self.assertEqual(model.Report.count(), 2)

        u.config['num_recipients'] = 2
        u.config['num_sites'] = 2
        Session.commit()

        r = self.call_api('report.create', remote_id=u'200002')
        r = self.call_api('subscription.create', report_id=report_id, email='foo@example.com', display_name='Foo')

        self.assertEqual(model.User.count(), 2)
        self.assertEqual(model.Report.count(), 3)


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

        r = model.Report(type='activity-month')
        self.assertEqual(r.next_preferred(now), datetime.datetime(2013, 2, 1, 13, 0, 0))
        self.assertEqual(r.next_preferred(datetime.date(2013, 2, 2)), datetime.datetime(2013, 3, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2013, 2, 1)), datetime.datetime(2013, 3, 1, 13))
        self.assertEqual(r.next_preferred(datetime.date(2013, 2, 28)), datetime.datetime(2013, 3, 1, 13))


class TestReportLib(test.TestCase):
    def _create_report_model(self, type='day'):
        return model.Report(
            remote_id=1,
            remote_data={},
            display_name='example.com',
            type=type,
        )

    def test_daily(self):
        report = self._create_report_model('day')
        since_time = datetime.datetime(2013, 1, 2)

        r = get_report('day')(report, since_time)

        self.assertEqual(r.date_end, datetime.date(2013, 1, 1))
        self.assertEqual(r.date_next, datetime.date(2013, 1, 2))
        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 1)")

    def test_activity_report(self):
        report = self._create_report_model('week')
        since_time = datetime.datetime(2013, 1, 14) # Monday after Next Sunday
        r = get_report('week')(report, since_time)

        self.assertEqual(r.date_start, datetime.date(2013, 1, 6)) # First Sunday
        self.assertEqual(r.date_end, datetime.date(2013, 1, 12)) # Next Saturday
        self.assertEqual(r.date_next, datetime.date(2013, 1, 21)) # Week from Monday

        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 6-12)")

        # Scenario: Overlapping month
        since_time = datetime.datetime(2013, 2, 4) # Monday after Next Saturday
        r = get_report('week')(report, since_time)

        self.assertEqual(r.date_start, datetime.date(2013, 1, 27)) # Last Sunday
        self.assertEqual(r.date_end, datetime.date(2013, 2, 2)) # Next Saturday
        self.assertEqual(r.date_next, datetime.date(2013, 2, 11)) # Week from Monday

        self.assertEqual(r.get_subject(), u"Report for example.com (Jan 27-Feb 2)")

        # Monthly activity report
        since_time = datetime.datetime(2013, 2, 5)
        report = self._create_report_model('activity-month')
        r = get_report('activity-month')(report, since_time)

        self.assertEqual(r.report.type, 'activity-month')
        self.assertEqual(r.date_start, datetime.date(2013, 1, 1)) # Start of the month
        self.assertEqual(r.date_end, datetime.date(2013, 1, 31)) # End of the month
        self.assertEqual(r.date_next, datetime.date(2013, 3, 1)) # First day of next month

        self.assertEqual(r.get_subject(), u"Report for example.com (January)")

    def test_trends_report(self):
        report = self._create_report_model('month')
        report.set_time_preferred(weekday=0) # Preferred time: First Monday

        since_time = datetime.datetime(2014, 1, 6) # First Monday of January 2014
        r = get_report('month')(report, since_time)

        self.assertEqual(r.report.type, 'month')
        self.assertEqual(r.date_start, datetime.date(2013, 12, 1)) # Start of December 2013
        self.assertEqual(r.date_end, datetime.date(2013, 12, 31)) # End of December 2013
        self.assertEqual(r.date_next, datetime.date(2014, 2, 3)) # First Monday of February 2014

        self.assertEqual(r.get_subject(), u"Report for example.com (December)")

        # Scenario: Month starting with Monday (Sept 1)
        since_time = datetime.datetime(2014, 8, 4)
        r = get_report('month')(report, since_time)

        self.assertEqual(r.date_start, datetime.date(2014, 7, 1))
        self.assertEqual(r.date_end, datetime.date(2014, 7, 31))
        self.assertEqual(r.date_next, datetime.date(2014, 9, 1)) # First day of September 2014

        self.assertEqual(r.get_subject(), u"Report for example.com (July)")

    def test_month_range(self):
        report = self._create_report_model('activity-month')
        since_time = datetime.datetime(2013, 2, 15)
        r = get_report('activity-month')(report, since_time)

        previous_date_start, date_start, date_end, date_next = r.get_date_range(since_time)
        self.assertEqual(previous_date_start, datetime.date(2012, 12, 1))
        self.assertEqual(date_start, datetime.date(2013, 1, 1))
        self.assertEqual(date_end, datetime.date(2013, 1, 31))
        self.assertEqual(date_next, datetime.date(2013, 3, 1))
