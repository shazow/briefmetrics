class Plan(object):

    def __init__(self, id, name, price, features, is_hidden=False):
        self.id = id
        self.name = name
        self.price = price
        self.features = features
        self.is_hidden = is_hidden

    def __str__(self):
        return self.id


PLANS = [

    Plan('trial', 'Trial', 0, {
        'num_emails': 3,
        'num_sites': 1,
    }, is_hidden=True),

    Plan('personal', 'Paid', 8.0, {
        'num_emails': None,
        'num_sites': None,
    }, is_hidden=True),

]


PLANS_LOOKUP = dict((p.id, p) for p in PLANS)
