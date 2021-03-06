from collections import OrderedDict
from dateutil.relativedelta import relativedelta


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
    def all(cls):
        return cls._singleton.items()

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
    Feature.new('combine_reports', 'Combined Reports'),
    Feature.new('email_domain', 'Your Domain'),
    Feature.new('self_hosted', 'Your Server'),
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

    def __init__(self, id, name, summary=None, price_monthly=None, price_yearly=None, features=None, is_hidden=False):
        self.id = id
        self.name = name
        self.summary = summary
        self.price_yearly = price_yearly
        if price_yearly and not price_monthly:
            price_monthly = round(price_yearly / 12.0)

        self.price_monthly = price_monthly
        self.features = OrderedDict()
        self.is_hidden = is_hidden

        self.price = price_monthly
        self.interval = relativedelta(months=1)
        if price_yearly:
            self.price = price_yearly
            self.interval = relativedelta(years=1)

        self.features.update(self.default_features)
        self.features.update(features)

        self.set(id, self)

    @property
    def stripe_interval(self):
        if self.price_yearly:
            return 'year'
        return 'month'

    @property
    def stripe_amount(self):
        if self.price_yearly:
            return int(self.price_yearly)
        return int(self.price_monthly)

    @property
    def price_monthly_str(self):
        if not self.price_monthly:
            return 'Free'

        return '${0:g}'.format(self.price_monthly / 100.0)

    @property
    def price_str(self):
        if not self.price_monthly:
            return 'Free'

        if self.price_yearly:
            return '${0:g}/year'.format(self.price_yearly / 100.0)

        return '${0:g}/month'.format(self.price_monthly / 100.0)

    @property
    def option_str(self):
        return '{plan.name} for {plan.price_str}'.format(plan=self)

    def iter_features(self):
        for key, value in self.features.items():
            yield Feature.get(key), value

    def __repr__(self):
        return 'Plan("{plan.id}", price="{plan.price_str}")'.format(plan=self)


class PlanGroup(Plan):
    # Similar to a Plan but with overrides for display purposes
    _singleton = {}
    is_group = True

    def __init__(self, id, name, summary=None, price_monthly=None, price_yearly=None, features=None, is_hidden=False, plans=None):
        self.id = id
        self.name = name
        self.summary = summary
        self.price_yearly = price_yearly if price_yearly else plans and plans[0].price_yearly
        if price_yearly and not price_monthly:
            price_monthly = round(price_yearly / 12.0)
        self.price_monthly = price_monthly if price_monthly else plans and plans[0].price_monthly
        self.features = OrderedDict(self.default_features)
        self.is_hidden = is_hidden
        self.plans = plans

        if plans:
            self.features.update(plans[0].features)
            for p in plans:
                p.in_group = self

        self.features.update(features)


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

    Plan.new('starter-yr', 'Starter', price_yearly=8000, features=[
        Feature.value('num_sites', 5),
    ]),

    # Agency plans

    Plan.new('agency-10', 'Agency (10 sites)', price_monthly=3500, features=[
        Feature.value('num_sites', 10),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ]),

    Plan.new('agency-10-yr', 'Agency (10 sites)', price_yearly=35000, features=[
        Feature.value('num_sites', 10),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ]),

    Plan.new('agency-25', 'Agency (25 sites)', price_monthly=8500, features=[
        Feature.value('num_sites', 25),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ]),

    Plan.new('agency-25-yr', 'Agency (25 sites)', price_yearly=85000, features=[
        Feature.value('num_sites', 25),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ]),

    Plan.new('agency-50', 'Agency (50 sites)', price_monthly=15000, features=[
        Feature.value('num_sites', 50),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ]),

    Plan.new('agency-50-yr', 'Agency (50 sites)', price_yearly=150000, features=[
        Feature.value('num_sites', 50),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ]),


    # Old:

    Plan.new('personal', 'Early Bird', 'For startups and hobbyists', price_monthly=800, features=[
    ], is_hidden=True),

    Plan.new('agency-small', 'Small Agency', '10 branded properties', price_monthly=3500, features=[
        Feature.value('num_sites', 10),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ], is_hidden=True),

    Plan.new('agency', 'Agency', '50 branded properties', price_monthly=15000, features=[
        Feature.value('num_sites', 50),
        Feature.value('custom_branding', True),
        Feature.value('combine_reports', True),
    ], is_hidden=True),
]


PlanGroup.new('agency-10', 'Agency', features=[
    Feature.value('num_sites', '10+'),
], plans=[
    Plan.get('agency-10'),
    Plan.get('agency-25'),
    Plan.get('agency-50'),
])

PlanGroup.new('agency-10-yr', 'Agency', features=[
    Feature.value('num_sites', '10+'),
], plans=[
    Plan.get('agency-10-yr'),
    Plan.get('agency-25-yr'),
    Plan.get('agency-50-yr'),
])

PlanGroup.new('enterprise', 'Enterprise', price_monthly=27500, features=[
    Feature.value('custom_branding', True),
    Feature.value('combine_reports', True),
    Feature.value('email_domain', True),
    Feature.value('self_hosted', True),
    Feature.value('support', 'Email & Phone'),
], is_hidden=True),

PlanGroup.new('enterprise-yr', 'Enterprise', price_yearly=275000, features=[
    Feature.value('custom_branding', True),
    Feature.value('combine_reports', True),
    Feature.value('email_domain', True),
    Feature.value('self_hosted', True),
    Feature.value('support', 'Email & Phone'),
], is_hidden=True),


PLANS_LOOKUP = dict((p.id, p) for p in PLANS)
PLAN_PAID = next(p for p in PLANS if p.price_monthly and not p.is_hidden)
PLAN_DEFAULT = Plan.get('starter')


def get_plan(plan_id):
    # TODO: Deprecate this?
    return Plan.get(plan_id)
