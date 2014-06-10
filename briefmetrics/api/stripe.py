from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from briefmetrics.web.environment import httpexceptions
from briefmetrics.lib.exceptions import APIError
from briefmetrics.lib.oauth import OAuth2API
from briefmetrics import model

from . import account as api_account


class StripeAPI(OAuth2API):
    config = {
        'auth_url': 'https://connect.stripe.com/oauth/authorize',
        'token_url': 'https://connect.stripe.com/oauth/token',
        'scope': 'read',

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }


def connect_user(request):
    code = request.params.get('code')
    if not code:
        raise httpexceptions.HTTPBadRequest('Missing code.')

    error = request.params.get('error')
    if error:
        raise APIError('Failed to connect: %s' % error)

    user = api_account.get_user(request, required=True)

    oauth = StripeAPI(request, state=request.session.get('oauth_state'))
    url = request.current_route_url().replace('http://', 'https://') # We lie, because honeybadger.

    try:
        token = oauth.auth_token(url)
    except InvalidGrantError:  # Try again.
        raise httpexceptions.HTTPSeeOther(request.route_path('account_login', service='stripe'))

    user.token = token
    model.Session.commit()
