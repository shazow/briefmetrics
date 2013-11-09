class Plan(object):

    def __init__(self, id, name, summary, features, price_monthly=None, is_hidden=False):
        self.id = id
        self.name = name
        self.summary = summary
        self.price_monthly = price_monthly
        self.features = features
        self.is_hidden = is_hidden

    def __str__(self):
        return self.id

    @property
    def price_monthly_str(self):
        if not self.price_monthly:
            return 'Free'

        return '${0:g}'.format(self.price_monthly / 100.0)

    @property
    def option_str(self):
        return '{plan.name} for {plan.price_monthly_str}/month: {plan.summary}'.format(plan=self)



PLANS = [

    Plan('trial', 'Trial', '3 free emails for one site', {
        'num_emails': 3,
        'num_sites': 1,
    }, is_hidden=True),

    Plan('free', 'Free', 'Super special free plan', {
        'num_emails': None,
        'num_sites': None,
    }, is_hidden=True),

    Plan('personal', 'Early Bird', 'Unlimited emails', {
        'num_emails': None,
        'num_sites': None,
    }, price_monthly=800),

]


PLANS_LOOKUP = dict((p.id, p) for p in PLANS)
PLAN_FREE = PLANS[0]
PLAN_PAID = next(p for p in PLANS if p.price_monthly and not p.is_hidden)
