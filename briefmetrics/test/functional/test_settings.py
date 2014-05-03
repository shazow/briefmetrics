from briefmetrics import test
from briefmetrics import api
from briefmetrics import model

from briefmetrics.test.fixtures.api_google import FakeQuery
import mock


Session = model.Session


@mock.patch('briefmetrics.api.google.Query', FakeQuery)
class TestSettings(test.TestWeb):

    def test_payment_set(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        r = self.app.get('/settings')
        self.assertIn('Account', r)
        self.assertIn('Add a credit card', r)

        r = self.call_api('settings.payments_set', plan_id=u'personal')
        self.assertEqual(model.User.get(u.id).plan_id, u'personal')

        r = self.call_api('settings.payments_set', plan_id=u'agency-small')
        self.assertEqual(model.User.get(u.id).plan_id, u'agency-small')

        r = self.app.get('/settings')
        self.assertIn('Agency', r)


    def test_choose_plan(self):
        # Set plan before signing up
        r = self.app.get('/pricing')
        r = self.call_api('settings.plan', plan_id=u'agency-10', format='redirect')
        self.assertIn('/account/login?next=%2Fsettings', r.location)

        r.follow()

        # Create account and login
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        u = model.User.get(1)
        self.assertEqual(u.plan_id, 'trial')
        trial_plan = u.plan

        # Visit settings to trigger plan change
        r = self.app.get('/settings')

        u = model.User.get(1)
        self.assertEqual(u.plan_id, u'agency-10')
        self.assertEqual(u.num_remaining, trial_plan.features.get('num_emails'))

        # Change plan now again
        r = self.call_api('settings.plan', plan_id=u'starter')

        # Already logged in, so don't need to visit settings to trigger.
        u = model.User.get(1)
        self.assertEqual(u.plan_id, u'starter')
        self.assertEqual(u.num_remaining, trial_plan.features.get('num_emails'))
