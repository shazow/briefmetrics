from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics import tasks

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

    def test_fetch_weekly(self):
        report = self._create_report()

        context = api.report.fetch_weekly(self.request, report, datetime.date(2013, 1, 6))
        self.assertEqual(context.date_end, datetime.date(2013, 1, 12))
        self.assertEqual(context.date_next, datetime.date(2013, 1, 21))
        self.assertEqual(context.subject, u'Weekly report \u2019til Jan 12: example.com')

        html = api.report.render_weekly(self.request, report.account.user, context)
        self.assertTrue(html)

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
            self.assertFalse(send_message.called)

        # Report should be deleted.
        self.assertEqual(model.Report.count(), 0)
        self.assertEqual(model.ReportLog.count(), 1)

        model.Session.refresh(user)
        self.assertEqual(user.num_remaining, 0)
