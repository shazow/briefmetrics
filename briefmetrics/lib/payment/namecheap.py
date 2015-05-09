import logging

from .base import Payment, PaymentError

from unstdlib import now
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.service import registry as service_registry
from dateutil.relativedelta import relativedelta


log = logging.getLogger(__name__)


class NamecheapPayment(Payment):
    id = "namecheap"
    auto_charge = relativedelta(seconds=1) # Truthy.

    @property
    def is_charging(self):
        return bool(self.user.time_next_payment)

    def set(self, new_token=None, metadata=None):
        if new_token:
            self.user.set_payment('namecheap', new_token)
        if not self.user.time_next_payment:
            self.user.time_next_payment = now()

    def start(self):
        if not self.token:
            raise PaymentError("Cannot start subscription for user without a payment method: %s" % self.user.id)

        if not self.user.plan_id:
            raise PaymentError("Cannot start subscription for user without a confirmed plan: %s" % self.user.id)

        if not self.user.time_next_payment or self.user.time_next_payment < now():
            # Too early to charge, skip the rest.
            return

        plan = self.user.plan
        amount = plan.price
        description = "Briefmetrics: %s" % plan.option_str
        self.invoice(amount, description=description)

        next_payment = self.user.time_next_payment or now()
        next_payment += plan.interval

        self.user.time_next_payment = next_payment

    def prorate(self, old_plan=None, new_plan=None, since_time=None, time_next_payment=None):
        if not since_time:
            since_time = now()

        if not time_next_payment:
            time_next_payment = self.user.time_next_payment
        if not time_next_payment:
            return 0.0

        if not old_plan:
            old_plan = self.user.plan
        if not old_plan:
            return 0.0

        amount = (new_plan or old_plan).price
        if time_next_payment < since_time:
            return amount

        last_payment = time_next_payment - old_plan.interval
        days_paid = (since_time - last_payment).days
        days_total = (time_next_payment - last_payment).days
        used = (float(days_paid) / float(days_total)) * old_plan.price

        amount = used - old_plan.price
        if new_plan:
            amount = new_plan.price - used

        log.debug("prorate (user_id={user_id}): {old_price} -> {new_price} over {days_paid}/{days_total} = {amount}".format(
            user_id=self.user and self.user.id,
            old_price=old_plan.price,
            new_price=new_plan and new_plan.price,
            days_paid=days_paid,
            days_total=days_total,
            amount=amount
        ))

        return amount


    def delete(self):
        p = self.user.payment
        if not p:
            # Nothing to delete
            return

        assert p.id == 'namecheap'
        self.user.payment_token = None

    def invoice(self, amount, description):
        amount_dollars = '%0.2f' % round(amount / 100, 2)
        # Make payment
        nc = service_registry['namecheap'].instance

        # Create invoice
        r = nc.request('POST', '/v1/billing/invoice', data={
            'subscription_id': self.token,
        })
        assert_response(r)
        data = r.json()
        invoice_id = data['result']['id']

        # Add line item
        item = {
            'description' : description,
            'amount': amount_dollars,
            'taxable': 0,
        }
        r = nc.request('POST', '/v1/billing/invoice/{invoice_id}/line_items'.format(invoice_id=invoice_id), json=item)
        assert_response(r)

        # Submit payment
        r = nc.request('POST', '/v1/billing/invoice/{invoice_id}/payments'.format(invoice_id=invoice_id), json={})
        assert_response(r)
        data = r.json()

        log.info("Namecheap invoice ${amount}: {user}; {data}".format(user=self.user, amount=amount_dollars, data=data))

        if data['result']['status'] == 'failed':
            raise PaymentError('Failed to invoice')
