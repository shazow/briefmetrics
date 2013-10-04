import time
import inspect

from requests_oauthlib import OAuth2Session
from dogpile.cache import make_region

from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError


def make_key_generator(namespace, fn):
    spec = inspect.getargs(fn.__code__).args

    def generate_key(*arg, **kw):
        kw.update(zip(spec, arg))
        kw.pop('self', None)

        key = (namespace or '') + ':' + ':'.join(str(kw[k]) for k in sorted(kw))
        return key
    return generate_key


report_cache = make_region(
    function_key_generator=make_key_generator,
).configure(
    'dogpile.cache.dbm',
    arguments = {
        "filename": "report_cache.dbm"
    }
)

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
        token = _clean_token(new_token)

        old_token.update(token)
        Session.commit()

    return wrapped


def auth_session(request, token=None, state=None):
    if token and 'expires_at' in token:
        token['expires_in'] = int(token['expires_at'] - time.time())

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


def _clean_token(token):
    return {
        'access_token': token['access_token'],
        'token_type': token['token_type'],
        'refresh_token': token['refresh_token'],
        'expires_at': int(time.time() + token['expires_in']),
    }


def auth_token(oauth, response_url):
    token = oauth.fetch_token(
        oauth_config['token_url'],
        authorization_response=response_url,
        client_secret=oauth_config['client_secret'],
    )
    return _clean_token(token)


class Query(object):
    def __init__(self, oauth):
        self.api = oauth

    @report_cache.cache_on_arguments()
    def get_profiles(self, account_id):
        r = self.api.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles')
        r.raise_for_status()

        return r.json()

    @report_cache.cache_on_arguments()
    def report_summary(self, id, date_start, date_end):
        params = {
            'ids': 'ga:%s' % id,
            'start-date': date_start,
            'end-date': date_end,
            'metrics': 'ga:visits',
            'dimensions': 'ga:fullReferrer,ga:source,ga:medium',
            'sort': '-ga:visits',
            'max-results': '30',
        }
        r = self.api.get('https://www.googleapis.com/analytics/v3/data/ga', params=params)
        r.raise_for_status()

        return r.json()
