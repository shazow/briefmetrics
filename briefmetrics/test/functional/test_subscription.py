from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics import tasks
from briefmetrics.lib.report import Report, DailyReport, WeeklyReport, MonthlyReport
from briefmetrics.lib.table import Column
from briefmetrics.lib.controller import Context

from briefmetrics.test.fixtures.api_google import FakeQuery

import mock
import datetime

Session = model.Session


@mock.patch('briefmetrics.api.google.Query', FakeQuery)
class TestSubscription(test.TestWeb):
    def test_repeated_subscription(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))
        r = self.call_api('report.create', remote_id=u'111112')

        self.assertEqual(model.User.count(), 1)
        self.assertEqual(model.Subscription.count(), 1)

        report_id = r['result']['report']['id']
        r = self.call_api('subscription.create', report_id=report_id, email='foo@example.com', display_name='Foo')

        self.assertEqual(model.User.count(), 2)
        self.assertEqual(model.Subscription.count(), 2)

        r = self.call_api('subscription.create', report_id=report_id, email='foo@example.com', display_name='Bar')

        self.assertEqual(model.User.count(), 2)
        self.assertEqual(model.Subscription.count(), 2)

        # Second subscription create should not override the first.
        new_user = model.User.get(2)
        self.assertEqual(new_user.display_name, 'Foo')
