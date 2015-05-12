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
        if self.token:
            customer = stripe.Customer.retrieve(self.token)
            customer.delete()
            user.stripe_customer_id = None
            user.payment_token = None


# Old helpers, do something with them?
'''
def sync_plans(pretend=True, include_hidden=False):
    if pretend:
        print "(Running in pretend mode)"

    local_plans = set(key for key, plan in pricing.Plan.all() if not plan.is_hidden)

    r = stripe.Plan.all()
    for plan in r.data:
        try:
            local_plan_id = plan.id.split('briefmetrics_', 1)[1]
        except IndexError, _:
            print "Invalid plan prefix: %s" % plan.id
            continue

        if local_plan_id not in local_plans:
            print "Plan missing locally: {}".format(local_plan_id)
            continue

        local_plans.remove(local_plan_id)
        local_plan = pricing.Plan.get(local_plan_id)

        if plan.amount != local_plan.price_monthly:
            print "Plan discrepency for '{id}': Remote amount {remote_amount}, local amount {local_amount}".format(
                id=plan.id,
                remote_amount=plan.amount,
                local_amount=local_plan.price_monthly,
            )

    for plan_id in local_plans:
        print "Plan missing remotely: {}".format(plan_id)
        if pretend:
            continue

        plan = pricing.Plan.get(plan_id)
        stripe.Plan.create(
            id=payment.StripePayment._plan_key(plan_id),
            amount=plan.price_monthly,
            interval='month',
            name='Briefmetrics: %s' % plan.name,
            currency='usd',
            statement_description='Briefmetrics',
        )


def sync_customers(pretend=True, only_plan=False):
    if pretend:
        print "(Running in pretend mode)"

    stripe_users = [u for u in model.User.all() if u.stripe_customer_id]

    for user in stripe_users:
        description = 'Briefmetrics User: %s' % user.email
        metadata = {'user_id': user.id}
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        customer.description = description
        customer.metadata = metadata
        customer.email = user.email

        set_plan = False
        if user.num_remaining is None:
            subscriptions = customer.subscriptions.all()
            set_plan = user.plan_id
            if not subscriptions.count:
                print "Plan missing: %r -> %s" % (user, user.plan_id)
            elif subscriptions.count > 1:
                print "Too many plans: %r -> %s -> %s" % (user, user.plan_id, ', '.join(d.plan.id for d in subscriptions.data))
            elif subscriptions.data[0].plan.id != payment.StripePayment._plan_key(user.plan_id):
                print "Wrong plan: %r -> %s -> %s" % (user, user.plan_id, ', '.join(d.plan.id for d in subscriptions.data))
            else:
                set_plan = False

        if pretend:
            continue

        print "Setting customer: {}".format(description)
        if set_plan:
            print "  Updating plan: {}".format(user.plan_id)
            customer.update_subscription(plan=payment.StripePayment._plan_key(user.plan_id))

        if only_plan:
            continue

        customer.save()

    print "Updated {} users.".format(len(stripe_users))
'''
