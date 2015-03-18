from briefmetrics.lib.exceptions import APIError
from briefmetrics.lib.registry import registry_metaclass

registry = {}

class PaymentError(APIError):
    pass


class Payment(object):
    __metaclass__ = registry_metaclass(registry)
    id = None

    def __init__(self, user, token=None):
        self.user = user
        self.token = token
