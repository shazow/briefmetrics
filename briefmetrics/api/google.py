from requests_oauthlib import OAuth2Session

from briefmetrics import model
from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError


oauth_config = {
    'auth_url': 'https://accounts.google.com/o/oauth2/auth',
    'token_url': 'https://accounts.google.com/o/oauth2/token',
    'scope': [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/analytics.readonly',
    ],

    # Populate these during setup:
    # 'client_id': ...,
    # 'client_secret': ...,
}

def _dict_view(d, keys):
    return {k: d[k] for k in keys}

def _token_updater(old_token):
    # TODO: Does this work?
    def wrapped(new_token):
        print "Updating refresh token?", new_token
        if not old_token:
            return

        old_token.update(new_token)
        Session.commit()


def auth_session(request, token=None, state=None):
    # TODO: Investigate if OAuth2Session reuses connections?
    return OAuth2Session(
        oauth_config['client_id'],
        redirect_uri=request.route_url('account_connect'),
        scope=oauth_config['scope'],
        auto_refresh_url=oauth_config['token_url'],
        auto_refresh_kwargs=_dict_view(oauth_config, ['client_id', 'client_secret']),
        token_updater=_token_updater(token),
        token=token,
        state=state,
    )


def auth_url(oauth):
    return oauth.authorization_url(
        oauth_config['auth_url'],
        access_type='offline', approval_prompt='force',
    )


def auth_token(oauth, response_url):
    return oauth.fetch_token(
        oauth_config['token_url'],
        authorization_response=response_url,
        client_secret=oauth_config['client_secret'],
    )


def get_profiles(request, account):
    g = auth_session(request, account.oauth_token)
    r = g.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles')
    r.raise_for_status()

    return r.json()
