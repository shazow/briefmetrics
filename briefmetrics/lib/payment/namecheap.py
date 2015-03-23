from .base import Payment, PaymentError


class NamecheapPayment(Payment):
    id = "namecheap"

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
            raise PaymentError(e.message)

    def start(self):
        if not self.token:
            raise PaymentError("Cannot start subscription for user without a payment method: %s" % self.user.id)

        user = self.user
        customer = stripe.Customer.retrieve(self.token)
        try:
            customer.update_subscription(plan=self._plan_key(user.plan_id))
        except stripe.CardError as e:
            self.delete()
            raise PaymentError('Failed to start payment plan: %s' % e.message)

    def delete(self):
        user = self.user
        if user.stripe_customer_id:
            customer = stripe.Customer.retrieve(self.token)
            customer.delete()
            user.stripe_customer_id = None
            user.payment_token = None

        if not user.num_remaining:
            user.num_remaining = 0
