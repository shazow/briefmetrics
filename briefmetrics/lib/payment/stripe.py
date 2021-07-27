from __future__ import absolute_import
import stripe

from .base import Payment, PaymentError


class StripePayment(Payment):
    id = "stripe"

    @staticmethod
    def _plan_key(plan_id):
        return 'briefmetrics_%s' % plan_id

    def set(self, new_token, metadata=None):
        user = self.user
        description = 'Briefmetrics User: %s' % user.email
        metadata = metadata or {}
        metadata.update({'user_id': user.id})

        try:
            if self.token:
                customer = stripe.Customer.retrieve(self.token)
                customer.card = new_token
                customer.description = description
                customer.metadata = metadata
                customer.save()
            else:
                customer = stripe.Customer.create(
                    card=new_token,
                    description=description,
                    email=user.email,
                    metadata=metadata,
                )
                user.stripe_customer_id = customer.id
                user.set_payment(self.id, customer.id)

        except stripe.error.CardError as e:
            raise PaymentError(str(e))

    def start(self):
        if not self.token:
            raise PaymentError("Cannot start subscription for user without a payment method: %s" % self.user.id)

        user = self.user
        plan_key = self._plan_key(user.plan_id)
        customer = stripe.Customer.retrieve(self.token)
        try:
            sub = customer.subscription
            if sub:
                sub_id = sub['id']
                stripe.Subscription.modify(sub_id, plan=plan_key) # TODO: migrate to 'price'
            else:
                stripe.Subscription.create(customer=customer['id'], items=[ {"plan": plan_key} ])
        except stripe.error.CardError as e:
            self.delete()
            raise PaymentError('Failed to start payment plan: %s' % e)
        except stripe.error.InvalidRequestError as e:
            raise PaymentError('Payment information is out of date. Please update your credit card before starting a plan.')

    def delete(self):
        user = self.user
        if self.token:
            customer = stripe.Customer.retrieve(self.token)
            customer.delete()
            user.stripe_customer_id = None
            user.payment_token = None
