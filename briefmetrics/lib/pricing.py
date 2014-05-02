class Plan(object):

    def __init__(self, id, name, summary=None, price_monthly=None, features=None, is_hidden=False):
        self.id = id
        self.name = name
        self.summary = summary
        self.price_monthly = price_monthly
        self.features = features or {}
        self.is_hidden = is_hidden

    def __str__(self):
        return self.id

    @property
    def price_monthly_str(self):
        if not self.price_monthly:
            return 'Free'

        return '${0:g}'.format(self.price_monthly / 100.0)

    @property
    def price_str(self):
        return self.price_monthly_str

    @property
    def option_str(self):
        return '{plan.name} for {plan.price_monthly_str}/month: {plan.summary}'.format(plan=self)



PLANS = [

    Plan('trial', 'Trial', '10 free email reports', features={
        'num_emails': 10,
    }, is_hidden=True),

    Plan('recipient', 'Recipient', '10 free email reports', features={
        'num_emails': 10,
    }, is_hidden=True),

    Plan('free', 'Free', 'Super special free plan', features={
    }, is_hidden=True),

    # Individual plans

    Plan('personal', 'Starter', 'For startups and hobbyists', price_monthly=800, features={
    }),

    # Agency plans

    Plan('agency-10', 'Agency (10 sites)', price_monthly=3500, features={
        'num_sites': 10,
        'custom_branding': True,
    }),

    Plan('agency-25', 'Agency (25 sites)', price_monthly=8500, features={
        'num_sites': 25,
        'custom_branding': True,
    }),

    Plan('agency-50', 'Agency (50 sites)', price_monthly=15000, features={
        'num_sites': 50,
        'custom_branding': True,
    }),

    # Enterprise plans (not used yet)

    Plan('enterprise', 'Enterprise', price_monthly=27500, features={
        'custom_branding': True,
        'advanced_reports': True,
    }, is_hidden=True),

    # Old:

    Plan('agency-small', 'Small Agency', '10 branded properties', price_monthly=3500, features={
        'num_sites': 10,
        'custom_branding': True,
    }, is_hidden=True),

    Plan('agency', 'Agency', '50 branded properties', price_monthly=15000, features={
        'num_sites': 50,
        'custom_branding': True,
    }, is_hidden=True),
]


PLANS_LOOKUP = dict((p.id, p) for p in PLANS)
PLAN_FREE = PLANS[0]
PLAN_PAID = next(p for p in PLANS if p.price_monthly and not p.is_hidden)


def get_plan(plan_id):
    return PLANS_LOOKUP[plan_id]
