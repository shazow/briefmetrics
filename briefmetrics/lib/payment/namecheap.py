import logging

from .base import Payment, PaymentError

from dateutil.relativedelta import relativedelta
from unstdlib import now
from briefmetrics.lib.service import registry as service_registry


log = logging.getLogger(__name__)


class NamecheapPayment(Payment):
    id = "namecheap"

    def set(self, new_token=None, metadata=None):
        if new_token:
            self.user.set_payment('namecheap', new_token)

    def start(self):
        if not self.token:
            raise PaymentError("Cannot start subscription for user without a payment method: %s" % self.user.id)

        if not self.plan_id:
            raise PaymentError("Cannot start subscription for user without a confirmed plan: %s" % self.user.id)

        if self.user.time_next_payment and self.user.time_next_payment < now():
            # Too early to charge, skip the rest.
            return

        amount = self.plan.price_yearly or self.plan.price_monthly
        description = "Briefmetrics: %s" % self.plan.option_str
        self.invoice(amount, description)

        next_payment = self.user.time_next_payment or now()
        if self.plan.price_yearly:
            next_payment += relativedelta(years=1)
        else:
            next_payment += relativedelta(months=1)

        self.user.time_next_payment = next_payment

    def delete(self):
        p = self.user.payment
        if not p:
            # Nothing to delete
            return

        assert p.id == 'namecheap'

        # TODO: Issue pro-rated refund?
        self.user.payment_token = None

    def invoice(self, amount, description):
        # Make payment
        nc = service_registry['namecheap'].instance

        # Create invoice
        r = nc.request('POST', '/v1/billing/invoice', data={
            'subscription_id': self.token,
        })
        data = r.json()
        invoice_id = data['result']['id']

        # Add line item
        item = {
            'description' : description,
            'amount': amount,
            'taxable': 0,
        }
        r = nc.request('POST', '/v1/billing/invoice/{invoice_id}/line_items'.format(invoice_id=invoice_id), json=item)

        # Submit payment
        r = nc.request('POST', '/v1/billing/invoice/{invoice_id}/payments'.format(invoice_id=invoice_id), json={})
        data = r.json()
        payment_id = data['result']['id']

        log.debug("Namecheap invoiced: {user}; amount={amount}; payment_id={payment_id}".format(user=self.user, amount=amount, payment_id=payment_id))
