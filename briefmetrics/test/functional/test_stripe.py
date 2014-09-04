import json

from briefmetrics import test
from briefmetrics.lib.service import stripe


STRIPE_WEBHOOKS = {
        'invoice.payment.succeeded': json.loads('''{ "id": "evt_4hjGt8Yo8rNkiq", "created": 1409674000, "livemode": true, "type": "invoice.payment_succeeded", "data": { "object": { "date": 1409670224, "id": "in_4hiFBbDjuLsJ6T", "period_start": 1406991643, "period_end": 1409670043, "lines": { "object": "list", "total_count": 1, "has_more": false, "url": "/v1/invoices/in_4hiFBbDjuLsJ6T/lines", "data": [ { "id": "sub_334KckxysYt43E", "object": "line_item", "type": "subscription", "livemode": true, "amount": 800, "currency": "usd", "proration": false, "period": { "start": 1409670043, "end": 1412262043 }, "quantity": 1, "plan": { "interval": "month", "name": "Briefmetrics: Personal", "created": 1382784955, "amount": 800, "currency": "usd", "id": "briefmetrics_personal", "object": "plan", "livemode": true, "interval_count": 1, "trial_period_days": null, "metadata": { }, "statement_description": "Briefmetrics" }, "description": null, "metadata": { } } ], "count": 1 }, "subtotal": 800, "total": 800, "customer": "cus_2x76h2AeyQBi2S", "object": "invoice", "attempted": true, "closed": true, "forgiven": false, "paid": true, "livemode": true, "attempt_count": 1, "amount_due": 800, "currency": "usd", "starting_balance": 0, "ending_balance": 0, "next_payment_attempt": null, "webhooks_delivered_at": 1409670226, "charge": "ch_4hjGX8kaVAVBWX", "discount": null, "application_fee": null, "subscription": "sub_334KckxysYt43E", "metadata": { }, "statement_description": null, "description": null } }, "object": "event", "pending_webhooks": 1, "request": null }'''),
}


class TestStripe(test.TestCase):
    def test_webhook_extract(self):
        w = STRIPE_WEBHOOKS['invoice.payment.succeeded']
        t = stripe.StripeAPI.extract_transaction(w)

        self.assertEqual(t, {
            'cu': u'USD',
            'hit_type': 'transaction',
            'items': [{'cu': u'USD',
                'hit_type': 'item',
                'in': u'Briefmetrics: Personal',
                'ip': 8.00,
                'iq': 1,
                'ti': u'in_4hiFBbDjuLsJ6T'}],
            'ti': u'in_4hiFBbDjuLsJ6T',
            'tr': 8.00})
