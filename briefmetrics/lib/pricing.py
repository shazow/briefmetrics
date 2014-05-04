from collections import OrderedDict


class Singleton(object):
    # TODO: Use a metaclass for singleton stuff?
    @classmethod
    def new(cls, id, *args, **kw):
        inst = cls(id, *args, **kw)
        cls.set(id, inst)
        return inst

    @classmethod
    def set(cls, id, inst):
        cls._singleton[id] = inst

    @classmethod
    def get(cls, id):
        return cls._singleton[id]

    @classmethod
    def value(cls, id, value):
        if id not in cls._singleton:
            raise KeyError('Invalid feature: %s' % id)
        return id, value

    def __str__(self):
        return self.id


class Feature(Singleton):
    _singleton = {}

    def __init__(self, id, name=None):
        self.id = id
        self.name = name


FEATURES = [
    Feature.new('num_emails', 'Email Reports'),
    Feature.new('num_sites', 'Websites'),
    Feature.new('num_recipients', 'Recipients'),
    Feature.new('custom_branding', 'Custom Branding'),
    Feature.new('email_domain', 'Your Domain'),
    Feature.new('support', 'Support'),
]


class Plan(Singleton):
    _singleton = {}
    is_group = False
    in_group = None

    default_features = [
        Feature.value('num_sites', None),
        Feature.value('num_recipients', None),
        Feature.value('support', 'Email'),
    ]

    def __init__(self, id, name, summary=None, price_monthly=None, features=None, is_hidden=False):
        self.id = id
        self.name = name
        self.summary = summary
        self.price_monthly = price_monthly
        self.features = OrderedDict()
        self.is_hidden = is_hidden

        self.features.update(self.default_features)
        self.features.update(features)

        self.set(id, self)

    @property
    def price_monthly_str(self):
        if not self.price_monthly:
            return 'Free'

        return '${0:g}'.format(self.price_monthly / 100.0)

    @property
    def price_str(self):
        if not self.price_monthly:
            return 'Free'

        return '${0:g}/month'.format(self.price_monthly / 100.0)

    @property
    def option_str(self):
        return '{plan.name} for {plan.price_monthly_str}/month: {plan.summary}'.format(plan=self)

    def iter_features(self):
        for key, value in self.features.iteritems():
            yield Feature.get(key), value


class PlanGroup(Plan):
    # Similar to a Plan but with overrides for display purposes
    _singleton = {}
    is_group = True

    def __init__(self, id, name, summary=None, price_monthly=None, features=None, is_hidden=False, plans=None):
        self.id = id
        self.name = name
        self.summary = summary
        self.price_monthly = price_monthly if price_monthly else plans and plans[0].price_monthly
        self.features = OrderedDict(self.default_features)
        self.is_hidden = is_hidden
        self.plans = plans

        if plans:
            self.features.update(plans[0].features)
            for p in plans:
                p.in_group = self

        self.features.update(features)

    @property
    def price_str(self):
        return 'Starting at ${0:g}/month'.format(self.price_monthly / 100.0)


PLANS = [

    Plan.new('trial', 'Trial', '10 free email reports', features=[
        Feature.value('num_emails', 10),
    ], is_hidden=True),

    Plan.new('recipient', 'Recipient', '10 free email reports', features=[
        Feature.value('num_emails', 10),
    ], is_hidden=True),

    Plan.new('free', 'Free', 'Super special free plan', features=[
    ], is_hidden=True),

    # Individual plans

    Plan.new('starter', 'Starter', price_monthly=800, features=[
        Feature.value('num_sites', 5),
    ]),

    # Agency plans

    Plan.new('agency-10', 'Agency (10 sites)', price_monthly=3500, features=[
        Feature.value('num_sites', 10),
        Feature.value('custom_branding', True),
    ]),

    Plan.new('agency-25', 'Agency (25 sites)', price_monthly=8500, features=[
        Feature.value('num_sites', 25),
        Feature.value('custom_branding', True),
    ]),

    Plan.new('agency-50', 'Agency (50 sites)', price_monthly=15000, features=[
        Feature.value('num_sites', 50),
        Feature.value('custom_branding', True),
    ]),


    # Old:

    Plan.new('personal', 'Early Bird', 'For startups and hobbyists', price_monthly=800, features=[
    ]),

    Plan.new('agency-small', 'Small Agency', '10 branded properties', price_monthly=3500, features=[
        Feature.value('num_sites', 10),
        Feature.value('custom_branding', True),
    ], is_hidden=True),

    Plan.new('agency', 'Agency', '50 branded properties', price_monthly=15000, features=[
        Feature.value('num_sites', 50),
        Feature.value('custom_branding', True),
    ], is_hidden=True),
]


PlanGroup.new('agency-10', 'Agency', features=[
    Feature.value('num_sites', '10+'),
], plans=[
    Plan.get('agency-10'),
    Plan.get('agency-25'),
    Plan.get('agency-50'),
])

PlanGroup.new('enterprise', 'Enterprise', price_monthly=27500, features=[
    Feature.value('custom_branding', True),
    Feature.value('email_domain', True),
    Feature.value('support', 'Email & Phone'),
], is_hidden=True),



PLANS_LOOKUP = dict((p.id, p) for p in PLANS)
PLAN_PAID = next(p for p in PLANS if p.price_monthly and not p.is_hidden)
PLAN_DEFAULT = Plan.get('starter')


def get_plan(plan_id):
    # TODO: Deprecate this?
    return Plan.get(plan_id)
