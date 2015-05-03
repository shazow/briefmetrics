from briefmetrics import test
from briefmetrics import model
from briefmetrics.lib.service import registry as service_registry
from briefmetrics.lib.payment import registry as payment_registry

import mock
import json

Session = model.Session


RESPONSES = {
    'webhook': '{"event_token": "foo"}',
    'subscription_create': '{"type": "subscription_create", "event": {"returnURI": "https://api.sandbox.partners.namecheap.com/v1/saas/saas/eventResponse/67e2b7f7dcad46cfa4e2013f224fcead", "id": "b17055ca229140309e0a54df7804fb85", "user": {"username": "testuser", "email": "foo@localhost", "first_name": "bar", "last_name": "baz"}, "subscription_id": "308", "configuration": {}, "order": {"pricing_plan_sku": "starter-yr"}}}',
    'subscription_alter': '{"type": "subscription_alter", "event": {"returnURI": "https://api.sandbox.partners.namecheap.com/v1/saas/saas/eventResponse/75b060232a414c1084bd895e263a6bd5", "id": "a2a4e6a43fc74780b585413ea21780c1", "user": {"username": "testuser", "first_name": "bar", "last_name": "baz", "email": "bar@localhost"}, "subscription_id": 357, "configuration": {}, "order": {"product_sku": null, "pricing_plan_sku": "agency-10-yr", "pricing_plan_id": "3", "product_id": 257}}}',
}

class FakeNamecheapAPI(object):
    id = 'fake-namecheap'
    resp = {
        ('GET', '/v1/saas/saas/event/fakecreate'): RESPONSES['subscription_create'],
        ('GET', '/v1/saas/saas/event/fakealter'): RESPONSES['subscription_alter'],
    }
    session = mock.Mock()

    config = {
        'client_id': 'testing',
    }

    def request(self, method, url, *args, **kw):
        m = mock.Mock()
        m.json.return_value = json.loads(self.resp[(method, url)])
        return m


@mock.patch('briefmetrics.lib.service.namecheap.NamecheapAPI.instance', FakeNamecheapAPI())
class TestNamecheap(test.TestWeb):
    def test_webhook_provison(self):
        self.assertIn('namecheap', service_registry)
        self.assertIn('namecheap', payment_registry)

        self.app.post('/webhook/namecheap', params='{"event_token": "fakecreate"}', content_type='application/json')

        # Check that user was provisioned
        users = model.User.all()
        self.assertEqual(len(users), 1)

        u = users[0] 
        self.assertEqual(u.email, 'foo@localhost')
        self.assertEqual(u.display_name, 'bar baz')
        self.assertEqual(u.plan_id, 'starter-yr')
        self.assertEqual(u.time_next_payment, None)

        p = u.payment
        self.assertEqual(p.id, 'namecheap')
        self.assertEqual(p.token, '308')

        a = u.get_account(service='namecheap')
        self.assertEqual(a.remote_id, 'testuser')

        self.app.post('/webhook/namecheap', params='{"event_token": "fakealter"}', content_type='application/json')

        users = model.User.all()
        self.assertEqual(len(users), 1)

        u = users[0] 
        self.assertEqual(u.plan_id, 'agency-10-yr')
        self.assertEqual(u.time_next_payment, None)

    def test_connect_decode(self):
        payload = '''id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vd3d3LnNhbmRib3gubmFtZWNoZWFwLmNvbS9hcHBzL3NzbyIsInN1YiI6ImRjdGVzdDAyIiwiYXVkIjoiMjMxQ0JGRTgtRjE2RS00Qzc5LTgyRTQtQTNERUNFMUYzQUVDIiwiZXhwIjoxNDMwMzMxNDgwLCJpYXQiOjE0MzAzMjc4ODAsIm5vbmNlIjoiTi0zNDU2Nzc2NTQzNDU2IiwiaHRfaGFzaCI6ImJTTW5FQkl0UjN0bUhpNHFFeFVuVmcifQ.j5uhaOsXhEoAGwOZFrLnoh5CNJtq7IZLCfDILJ8Qzhc&access_token=00138cea3b28d495ebca715ea47301cf&token_type=Bearer&expires_in=3600&sid=s%3aeeneT5DZTnXLhWmR-hGtsq-wqT-puM-z.gGwM1WIwrKYBCmZcNer%2bh%2b2MkY9yJdQjfdmVOyxIChc'''
        r = self.call_api('account.connect', service='namecheap', payload=payload)
        self.assertEqual(r['result']['decoded'], {
            'iss': 'http://www.sandbox.namecheap.com/apps/sso',
            'sub': 'dchambers',
            'aud': '231CBFE8-F16E-4C79-82E4-A3DECE1F3AEC',
            'exp': 1429846851,
            'iat': 1429843251,
            'nonce': 'N-3456776543456',
            'ht_hash': 'ChhqVgtXJWpcdCcAUDUqbw',
        })
