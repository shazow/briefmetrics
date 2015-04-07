from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics.lib.service.namecheap import NamecheapAPI

import mock
import json

Session = model.Session


RESPONSES = {
    'webhook': '{"event_token": "foo"}',
    'subscription_create': '{"type": "subscription_create", "event": {"returnURI": "https://api.sandbox.partners.namecheap.com/v1/saas/saas/eventResponse/67e2b7f7dcad46cfa4e2013f224fcead", "id": "b17055ca229140309e0a54df7804fb85", "user": {"username": "testuser", "id": "fooid", "email": "foo@localhost", "first_name": "bar", "last_name": "baz"}, "subscription_id": "308", "configuration": {}, "order": {"product_id": 17}}}',
}

class FakeNamecheapAPI(object):
    id = 'fake-namecheap'
    resp = {
        ('GET', '/v1/saas/saas/event/foo'): RESPONSES['subscription_create'],
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
        self.app.post('/webhook/namecheap', params=RESPONSES['webhook'], content_type='application/json')

        # Check that user was provisioned
        users = model.User.all()
        self.assertEqual(len(users), 1)

        u = users[0] 
        self.assertEqual(u.email, 'foo@localhost')
        self.assertEqual(u.display_name, 'bar baz')

        p = u.payment
        self.assertEqual(p.id, 'namecheap')
        self.assertEqual(p.token, '308')

        a = u.get_account(service='namecheap')
        self.assertEqual(a.remote_id, 'fooid')
