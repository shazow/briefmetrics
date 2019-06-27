from briefmetrics import api
from briefmetrics import test
from briefmetrics import model
from briefmetrics.lib.service import registry as service_registry
from briefmetrics.lib.payment import registry as payment_registry

from dateutil.relativedelta import relativedelta
import mock
import json
import logging
import datetime
from unittest import skip
from unstdlib import now

Session = model.Session

log = logging.getLogger(__name__)


RESPONSES = {
    'webhook': '{"event_token": "foo"}',
    'subscription_create': '{"type": "subscription_create", "event": {"returnURI": "https://example/v1/saas/saas/eventResponse/67e2b7f7dcad46cfa4e2013f224fcead", "id": "b17055ca229140309e0a54df7804fb85", "user": {"username": "testuser", "email": "foo@localhost", "first_name": "bar", "last_name": "baz"}, "subscription_id": "308", "configuration": {}, "order": {"pricing_plan_sku": "starter-yr"}}}',
    'subscription_alter': '{"type": "subscription_alter", "event": {"returnURI": "https://example/v1/saas/saas/eventResponse/75b060232a414c1084bd895e263a6bd5", "id": "a2a4e6a43fc74780b585413ea21780c1", "user": {"username": "testuser", "first_name": "bar", "last_name": "baz", "email": "bar@localhost"}, "subscription_id": 357, "configuration": {}, "order": {"product_sku": null, "pricing_plan_sku": "%(pricing_plan_sku)s", "pricing_plan_id": "3", "product_id": 257}}}',
}

class FakeNamecheapAPI(object):
    id = 'fake-namecheap'
    resp = {
        ('GET', '/v1/saas/saas/event/fakecreate'): RESPONSES['subscription_create'],
        ('GET', '/v1/saas/saas/event/badevent'): '["wtf?"]',
        ('GET', '/v1/saas/saas/event/fakealter'): RESPONSES['subscription_alter'] % dict(pricing_plan_sku='agency-10-yr'),
        ('GET', '/v1/saas/saas/event/fakealter2'): RESPONSES['subscription_alter'] % dict(pricing_plan_sku='starter-yr'),
        ('POST', '/v1/billing/invoice'): '{"result": {"status": "open", "status_id": "1", "created_at": "2015-05-07T01:30:29.923Z", "amount_due": null, "subscription_id": 1206, "id": "123"}}',
        ('POST', '/v1/billing/invoice/123/line_items'): '{}',
        ('POST', '/v1/billing/invoice/123/payments'): '{"result": {"status": "success"}}',
    }
    session = mock.Mock()

    config = {
        'client_id': 'testing',
    }

    def __init__(self):
        self.calls = []

    def query(self, method=None, url=None):
        r = self.calls
        if method:
            r = (c for c in r if c[0] == method)
        if url:
            r = (c for c in r if c[1] == url)

        return list(r)

    def request(self, method, url, *args, **kw):
        log.info('FakeNamecheapAPI.request: %s %s (%s, %s)', method, url, args, kw)
        self.calls.append((method, url, args, kw))
        m = mock.Mock()
        m.json.return_value = json.loads(self.resp[(method, url)])
        return m


@skip("disabled namecheap")
@mock.patch('briefmetrics.lib.service.namecheap.NamecheapAPI.instance', FakeNamecheapAPI())
class TestNamecheap(test.TestWeb):
    def test_connect_decode(self):
        api.account.get_or_create(
            email=u'foo@localhost',
            plan_id=u'starter-yr',
            service=u'namecheap',
            remote_id=u'shazow',
        )

        payload = '''id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vd3d3LnNhbmRib3gubmFtZWNoZWFwLmNvbS9hcHBzL3NzbyIsInN1YiI6InNoYXpvdyIsImF1ZCI6IjIzMUNCRkU4LUYxNkUtNEM3OS04MkU0LUEzREVDRTFGM0FFQyIsImV4cCI6MTQzMDY4MTY2MCwiaWF0IjoxNDMwNjc4MDYwLCJub25jZSI6IkVtQVJFUyIsImh0X2hhc2giOiJIMUFRSG10TktRSkxJeFpwQXlVQ0tRIn0.wPtPkJB1Y8AVe-u348qirxxjekz4olfXgyLjQx5VlLo&access_token=4a4422c8a3e3a95126d84131c6c1161f&token_type=Bearer&expires_in=3600&sid=s%3ao7GVoAsXfx8xAqe0X2BW6vQV5OrPNuOz.lRekL22%2fj673SlRu283JS9riFEDDx5cpoCXpb9cyou0'''
        r = self.call_api('account.connect', service='namecheap', payload=payload)
        self.assertEqual(r['result']['decoded'], {
            'aud': u'231CBFE8-F16E-4C79-82E4-A3DECE1F3AEC',
            'exp': 1430681660,
            'ht_hash': u'H1AQHmtNKQJLIxZpAyUCKQ',
            'iat': 1430678060,
            'iss': u'http://www.sandbox.namecheap.com/apps/sso',
            'nonce': u'EmARES',
            'sub': u'shazow',
        })

    def test_webhook_provison(self):
        self.assertIn('namecheap', service_registry)
        self.assertIn('namecheap', payment_registry)

        # Disable auto-charge
        restore_auto_charge, payment_registry['namecheap'].auto_charge = payment_registry['namecheap'].auto_charge, False

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            resp = self.app.post('/webhook/namecheap', params='{"event_token": "fakecreate"}', content_type='application/json')
            r = resp.json
            self.assertTrue(r['type'], 'subscription_create_resp')
            self.assertTrue(r['response']['state'], 'Active')

            self.assertTrue(send_message.called)
            self.assertEqual(len(send_message.call_args_list), 1)

            call = send_message.call_args_list[0]
            message = call[0][1].params
            self.assertIn(u"Welcome to Briefmetrics", message['subject'])

        # Check that user was provisioned
        users = model.User.all()
        self.assertEqual(len(users), 1)

        u = users[0] 
        self.assertEqual(u.email, 'foo@localhost')
        self.assertEqual(u.display_name, 'bar baz')
        self.assertEqual(u.plan_id, 'starter-yr')
        self.assertEqual(u.time_next_payment, None)
        self.assertEqual(u.payment.is_charging, False)

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

        u.time_next_payment = now()
        self.assertEqual(u.payment.is_charging, True)

        # Restore auto-charge
        payment_registry['namecheap'].auto_charge = restore_auto_charge

    def test_payment_collision(self):
        u = api.account.get_or_create(
            email=u'foo@localhost',
            plan_id=u'starter-yr',
            service=u'namecheap',
            remote_id=u'shazow',
        )

        u.set_payment('stripe', 'testtesttest')
        Session.commit()

        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            self.assertFalse(send_message.called)
            resp = self.app.post('/webhook/namecheap', params='{"event_token": "fakecreate"}', content_type='application/json')
            r = resp.json
            self.assertTrue(r['type'], 'subscription_create_resp')
            self.assertTrue(r['response']['state'], 'Failed')

    def test_prorate(self):
        base_time = datetime.datetime(2000, 1, 1)

        u = model.User()
        u.set_payment('namecheap', 'test')
        u.time_next_payment = base_time - relativedelta(months=1)
        u.plan_id = 'starter-yr'
        starter_plan = u.plan

        self.assertEqual(u.payment.prorate(since_time=base_time), starter_plan.price)

        u.time_next_payment = base_time + relativedelta(days=183)
        self.assertEqual(u.payment.prorate(since_time=base_time), -starter_plan.price/2)

        u.plan_id = 'agency-10-yr'
        agency_plan = u.plan
        self.assertEqual(u.payment.prorate(since_time=base_time, old_plan=starter_plan, new_plan=agency_plan), agency_plan.price-starter_plan.price/2)

        self.assertEqual(u.payment.prorate(since_time=base_time, old_plan=agency_plan, new_plan=None), -(agency_plan.price/2))


    def test_prorate_plan(self):
        with mock.patch('briefmetrics.api.email.send_message') as send_message:
            self.assertFalse(send_message.called)
            resp = self.app.post('/webhook/namecheap', params='{"event_token": "fakecreate"}', content_type='application/json')
            self.assertTrue(resp.json['response']['state'], 'Active')

        nc = service_registry['namecheap'].instance

        # Next payment in the past

        u = model.User.all()[0]
        u.num_remaining = None
        u.time_next_payment = now() - relativedelta(months=6)
        Session.commit()

        old_plan = u.plan
        self.app.post('/webhook/namecheap', params='{"event_token": "fakealter"}', content_type='application/json')
        new_plan = model.User.get(u.id).plan

        payments = nc.query(url='/v1/billing/invoice/123/payments')
        self.assertTrue(payments)

        line_items = nc.query(url='/v1/billing/invoice/123/line_items')
        print(line_items)
        line_item = line_items[0]

        params = line_item[-1]['json']
        self.assertEqual(params['amount'], '%0.2f' % (new_plan.price/100.0))

        # Next payment in the future

        nc.calls[:] = [] # Reset call log

        u = model.User.all()[0]
        u.num_remaining = None
        u.time_next_payment = now() + relativedelta(months=6)
        Session.commit()

        old_plan = u.plan
        self.app.post('/webhook/namecheap', params='{"event_token": "fakealter2"}', content_type='application/json')
        new_plan = model.User.get(u.id).plan

        payments = nc.query(url='/v1/billing/invoice/123/payments')
        self.assertTrue(payments)

        line_items = nc.query(url='/v1/billing/invoice/123/line_items')
        print(line_items)
        line_item = line_items[0]

        params = line_item[-1]['json']
        expected_amount = (new_plan.price - (old_plan.price / 2.0))/100.0
        self.assertLess(expected_amount, 0)
        delta = float(params['amount']) - expected_amount
        self.assertTrue(abs(delta) < 2, '%s !~= %s' % (params['amount'], expected_amount)) # This will vary by year, so we only approximate

    def test_webhook_fail(self):
        with self.assertRaises(AttributeError):
            self.app.post('/webhook/namecheap', params='["wtf"]', content_type='application/json')
