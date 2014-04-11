from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics import tasks
from briefmetrics.lib.report import Report, DailyReport, ActivityReport, TrendsReport
from briefmetrics.lib.table import Column
from briefmetrics.lib.controller import Context

import datetime

Session = model.Session


class TestSubscription(test.TestWeb):
    def test_repeated_subscription(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        r = self.call_api('settings.payments_set', plan_id=u'personal')
        self.assertEqual(model.User.get(u.id).plan_id, u'personal')

        r = self.call_api('settings.payments_set', plan_id=u'agency-small')
        self.assertEqual(model.User.get(u.id).plan_id, u'agency-small')
