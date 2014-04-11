from briefmetrics import test
from briefmetrics import api
from briefmetrics import model


Session = model.Session


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
