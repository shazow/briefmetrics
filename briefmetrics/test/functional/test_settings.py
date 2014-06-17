from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics.lib.image import get_cache_bust

from .test_image import LOGO_BYTES
from briefmetrics.test.fixtures.api_google import FakeQuery
import mock


Session = model.Session


@mock.patch('briefmetrics.lib.service.google.Query', FakeQuery)
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
        self.assertIn('/account/login/google?next=%2Fsettings', r.location)

        r.follow()

        # Create account and login
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        u = model.User.get(1)
        self.assertEqual(u.plan_id, 'trial')
        trial_plan = u.plan

        # Visit settings to trigger plan change
        r = self.app.get('/settings')
        self.assertIn('variations of the Agency plan', r)

        u = model.User.get(1)
        self.assertEqual(u.plan_id, u'agency-10')
        self.assertEqual(u.num_remaining, trial_plan.features.get('num_emails'))

        # Change plan now again
        r = self.call_api('settings.plan', plan_id=u'starter')
        self.assertNotIn('variations of the Agency plan', r)

        # Already logged in, so don't need to visit settings to trigger.
        u = model.User.get(1)
        self.assertEqual(u.plan_id, u'starter')
        self.assertEqual(u.num_remaining, trial_plan.features.get('num_emails'))

    def test_custom_branding(self):
        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        u.config['email_header_image'] = '1-foo.png?abc'
        Session.commit()

        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))
        r = self.call_api('settings.plan', plan_id=u'agency-10')
        r = self.call_api('settings.branding', plan_id=u'agency-10', _upload_files=[
            ('header_logo', 'fakefile.png', LOGO_BYTES),
        ])

        u = model.User.get(1)
        expected_name = '1-foo.png?' + get_cache_bust(LOGO_BYTES)
        self.assertEqual(u.config.get('email_header_image'), expected_name)

        r = self.call_api('settings.branding', plan_id=u'agency-10', _upload_files=[
            ('header_logo', 'fakefile.png', 'random garbage'),
        ], _status=400)

        # Make sure nothing changed.
        u = model.User.get(1)
        expected_name = '1-foo.png?' + get_cache_bust(LOGO_BYTES)
        self.assertEqual(u.config.get('email_header_image'), expected_name)
