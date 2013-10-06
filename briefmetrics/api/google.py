import time

from requests_oauthlib import OAuth2Session

from briefmetrics.model.meta import Session
from briefmetrics.lib.exceptions import APIError
from briefmetrics.lib.cache import ReportRegion


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


DATE_GA_FORMAT = '%Y-%m-%d'

class Query(object):
    def __init__(self, oauth):
        self.api = oauth

    @ReportRegion.cache_on_arguments()
    def get_profiles(self, account_id):
        # account_id used for caching, not in query.
        r = self.api.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles')
        r.raise_for_status()

        return r.json()

    @ReportRegion.cache_on_arguments()
    def report_summary(self, id, date_start, date_end):
        params = {
            'ids': 'ga:%s' % id,
            'start-date': date_start,
            'end-date': date_end,
            'metrics': 'ga:pageviews,ga:uniquePageviews,ga:timeOnSite',
        }
        r = self.api.get('https://www.googleapis.com/analytics/v3/data/ga', params=params)
        r.raise_for_status()
        return r.json()

    @ReportRegion.cache_on_arguments()
    def report_referrers(self, id, date_start, date_end):
        params = {
            'ids': 'ga:%s' % id,
            'start-date': date_start,
            'end-date': date_end,
            'metrics': 'ga:visits',
            'dimensions': 'ga:fullReferrer',
            'filter': 'ga:medium==referral',
            'sort': '-ga:visits',
            'max-results': '10',
        }
        r = self.api.get('https://www.googleapis.com/analytics/v3/data/ga', params=params)
        r.raise_for_status()
        return r.json()

    @ReportRegion.cache_on_arguments()
    def report_pages(self, id, date_start, date_end):
        params = {
            'ids': 'ga:%s' % id,
            'start-date': date_start,
            'end-date': date_end,
            'metrics': 'ga:pageviews',
            'dimensions': 'ga:pagePath',
            'sort': '-ga:pageviews',
            'max-results': '10',
        }
        r = self.api.get('https://www.googleapis.com/analytics/v3/data/ga', params=params)
        r.raise_for_status()
        return r.json()

    @ReportRegion.cache_on_arguments()
    def report_social(self, id, date_start, date_end):
        params = {
            'ids': 'ga:%s' % id,
            'start-date': date_start,
            'end-date': date_end,
            'metrics': 'ga:visits',
            'dimensions': 'ga:socialNetwork',
            'sort': '-ga:visits',
            'max-results': '5',
        }
        r = self.api.get('https://www.googleapis.com/analytics/v3/data/ga', params=params)
        r.raise_for_status()
        return r.json()
