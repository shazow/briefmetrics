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

    def set(self, new_token, metadata=None):
        raise NotImplementedError("Payment stub not implemented: %s.set", self.__class__.__name__)

    def start(self):
        raise NotImplementedError("Payment stub not implemented: %s.start", self.__class__.__name__)

    def delete(self):
        raise NotImplementedError("Payment stub not implemented: %s.delete", self.__class__.__name__)
