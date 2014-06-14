from .base import OAuth2API


class StripeAPI(OAuth2API):
    id = 'stripe'

    config = {
        'auth_url': 'https://connect.stripe.com/oauth/authorize',
        'token_url': 'https://connect.stripe.com/oauth/token',
        'scope': 'read',

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }
