import time

from requests_oauthlib import OAuth2Session

from briefmetrics.model.meta import Session
from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.table import Table


oauth_config = {
    'auth_url': 'https://accounts.google.com/o/oauth2/auth',
    'token_url': 'https://accounts.google.com/o/oauth2/token',
    'scope': [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/analytics.readonly',
    ],

    # Populate these during init:
    # 'client_id': ...,
    # 'client_secret': ...,
}

def _dict_view(d, keys):
    return {k: d[k] for k in keys}

def _token_updater(old_token):
    def wrapped(new_token):
        token = _clean_token(new_token)

        old_token.update(token)
        Session.commit()

    return wrapped

def _prune_abstract(label):
    if label.startswith('('):
        return
    return label

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


def create_query(request, oauth):
    if request.features.get('offline'):
        from briefmetrics.test.fixtures.api_google import FakeQuery
        return FakeQuery(oauth)

    return Query(oauth)


class Query(object):
    def __init__(self, oauth):
        self.api = oauth

    # NOTE: Expire by adding expiration_time=...

    @ReportRegion.cache_on_arguments()
    def _get(self, url, params=None, _cache_keys=None):
        r = self.api.get(url, params=params)
        assert_response(r)
        return r.json()

    def _get_data(self, params=None, _cache_keys=None):
        return self._get('https://www.googleapis.com/analytics/v3/data/ga', params=params, _cache_keys=_cache_keys)

    def _columns_to_params(self, params, dimensions=None, metrics=None):
        columns = []
        if dimensions:
            params['dimensions'] = ','.join(col.id for col in dimensions)
            columns += dimensions

        if metrics:
            params['metrics'] = ','.join(col.id for col in metrics)
            columns += metrics

        return columns

    def get_table(self, params, dimensions=None, metrics=None):
        params = dict(params)
        columns = self._columns_to_params(params, dimensions=dimensions, metrics=metrics)

        t = Table(columns)
        response_data = self._get_data(params)
        if 'rows' not in response_data:
            return t

        for row in response_data['rows']:
            t.add(row)

        return t

    def get_profiles(self, account_id):
        # account_id used for caching, not in query.
        return self._get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles', _cache_keys=(account_id,))
