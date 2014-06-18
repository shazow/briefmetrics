from .base import OAuth2API


class StripeAPI(OAuth2API):
    id = 'stripe'
    autocreate_report = 'stripe'

    config = {
        'auth_url': 'https://connect.stripe.com/oauth/authorize',
        'token_url': 'https://connect.stripe.com/oauth/token',
        'scope': ['read_only'],

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }

    def create_query(self):
        return Query(self.session)


class Query(object):
    def __init__(self, api):
        self.api = api

    def get(self, *args, **kw):
        return self.api.get(*args, **kw)
