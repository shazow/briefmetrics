import json
import mock

from briefmetrics import api
from briefmetrics import test
from briefmetrics import model
from briefmetrics.lib.service import stripe


STRIPE_WEBHOOKS = {
        'invoice.payment.succeeded': json.loads('''{ "id": "evt_4hjGt8Yo8rNkiq", "user_id": "acct_example", "created": 1409674000, "livemode": true, "type": "invoice.payment_succeeded", "data": { "object": { "date": 1409670224, "id": "in_4hiFBbDjuLsJ6T", "period_start": 1406991643, "period_end": 1409670043, "lines": { "object": "list", "total_count": 1, "has_more": false, "url": "/v1/invoices/in_4hiFBbDjuLsJ6T/lines", "data": [ { "id": "sub_334KckxysYt43E", "object": "line_item", "type": "subscription", "livemode": true, "amount": 800, "currency": "usd", "proration": false, "period": { "start": 1409670043, "end": 1412262043 }, "quantity": 1, "plan": { "interval": "month", "name": "Briefmetrics: Personal", "created": 1382784955, "amount": 800, "currency": "usd", "id": "briefmetrics_personal", "object": "plan", "livemode": true, "interval_count": 1, "trial_period_days": null, "metadata": { }, "statement_description": "Briefmetrics" }, "description": null, "metadata": { } } ], "count": 1 }, "subtotal": 800, "total": 800, "customer": "cus_2x76h2AeyQBi2S", "object": "invoice", "attempted": true, "closed": true, "forgiven": false, "paid": true, "livemode": true, "attempt_count": 1, "amount_due": 800, "currency": "usd", "starting_balance": 0, "ending_balance": 0, "next_payment_attempt": null, "webhooks_delivered_at": 1409670226, "charge": "ch_4hjGX8kaVAVBWX", "discount": null, "application_fee": null, "subscription": "sub_334KckxysYt43E", "metadata": { }, "statement_description": null, "description": null } }, "object": "event", "pending_webhooks": 1, "request": null }'''),
}


class TestStripeService(test.TestCase):
    def test_webhook_extract(self):
        w = STRIPE_WEBHOOKS['invoice.payment.succeeded']
        t = stripe.Query(None, None).extract_transaction(w, load_customer=False)

        self.assertEqual(t, {
            'cu': u'USD',
            'hit_type': 'transaction',
            'user_id': None,
            'items': [{'cu': u'USD',
                'hit_type': 'item',
                'user_id': None,
                'in': u'Briefmetrics: Personal',
                'ip': 8.00,
                'iq': 1,
                'ti': u'in_4hiFBbDjuLsJ6T'}],
            'ti': u'in_4hiFBbDjuLsJ6T',
            'tr': 8.00})


class TestStripe(test.TestWeb):
    def test_webhook(self):
        # Create account
        rando = api.account.get_or_create(service='stripe', email=u'rando@example.com', display_name=u'Rando', remote_id='acct_rando')
        rando_stripe = rando.get_account(service='stripe')

        # Create account
        u = api.account.get_or_create(service='google', email=u'example@example.com', display_name=u'Example')

        # Sign in
        r = self.call_api('account.login', token=u'%s-%d' % (u.email_token, u.id))

        # Connect Stripe
        u = api.account.get_or_create(service='stripe', email=u.email, display_name=u'Example', remote_id='acct_example')
        u_stripe = u.get_account(service='stripe')

        with mock.patch('briefmetrics.tasks.service.stripe_webhook.delay') as stripe_webhook:
            body = json.dumps(STRIPE_WEBHOOKS['invoice.payment.succeeded'])

            r = self.app.post('/webhook/stripe', params=body, content_type='application/json')
            self.assertFalse(stripe_webhook.called)

            # Create funnel
            r = self.call_api('funnel.create', _status=400, from_account_id=rando_stripe.id, ga_tracking_id='foo')
            r = self.call_api('funnel.create', _status=200, from_account_id=u_stripe.id, ga_tracking_id='foo')

            self.assertEqual(model.Account.get(rando_stripe.id).config, {})
            self.assertEqual(model.Account.get(u_stripe.id).config, {u'ga_funnels': [u'foo']})

            r = self.app.post('/webhook/stripe', params=body, content_type='application/json')
            self.assertTrue(stripe_webhook.called)

            call, = stripe_webhook.call_args_list
            self.assertEqual(call[0][0:2], (u'foo', u_stripe.id))

