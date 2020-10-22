import uuid
import requests
from urllib.parse import urlencode
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.exceptions import APIError
from briefmetrics.lib.table import Table
import briefmetrics.lib.helpers as h

from ..base import OAuth2API

from .activity import ActivityConcatReport, ActivityMonthlyReport, ActivityReport, ActivityYearlyReport
from .trends import TrendsReport
from .alerts import DailyReport
from .mobile import MobileWeeklyReport, MobileMonthlyReport

COLLECT_URL = 'https://ssl.google-analytics.com/collect'
COLLECT_SESSION = requests.Session()


def pretend_collect(*args, **kw):
    print("pretend_collect:", args, kw)


def collect(tracking_id, user_id=None, client_id=None, hit_type='pageview', http_session=COLLECT_SESSION, **kw):
    """

    collect('UA-407051-16', '1', hit_type='transaction', ti='test', tr='1.42', cu='USD')

    Page:
        hit_type='pageview'
        dp='/', # Page

    Transactions:
        hit_type='transaction',
        ti='...', # Transaction ID
        tr='...', # Transaction Revenue
        ta='...', # Transaction Affiliation.
        cu='USD', # Currency Code

    Transaction Item:
        hit_type='item',
        ti='12345',   # Transaction ID
        in='sofa',    # Item name. Required.
        ip='300',     # Item price.
        iq='2',       # Item quantity.
        ic='u3eqds4', # Item code / SKU.
        iv='furnitu', # Item variation / category.
        cu='EUR',     # Currency code.

    Events:
        hit_type='event',
        ec='...', # Event Category
        ea='...', # Event Action
        el='...', # Event Label
        ev='...', # Event Value

    Other:
        uip='1.2.3.4', # IP Override

    via https://developers.google.com/analytics/devguides/collection/protocol/v1/devguide
    """
    client_id = client_id or uuid.uuid4().hex
    params = {
        'v': 1, # Protocol version
        'tid': tracking_id, # Tracking ID (UA-XXXXXX-XX)
        'cid': client_id, # Client ID,
        'uid': user_id, # User ID,
        't': hit_type, # Hit Type
        'uip': '0.0.0.0', # IP Override
        'ni': 1, # Non-interactive
    }
    params.update(kw)

    req = requests.Request('POST', COLLECT_URL, data=urlencode(params, doseq=True)).prepare()
    resp = http_session.send(req)
    assert_response(resp)
    return resp


# FIXME: ... This is a temporary fix for scope change issues
def _monkeypatch_validate_token_parameters(params, scope=None):
    """Ensures token precence, token type, expiration and scope in params."""
    if 'error' in params:
        oauthlib.oauth2.rfc6749.parameters.raise_from_error(params.get('error'), params)

    if not 'access_token' in params:
        raise oauthlib.oauth2.rfc6749.parameters.MissingTokenError(description="Missing access token parameter.")

    if not 'token_type' in params:
        raise oauthlib.oauth2.rfc6749.parameters.MissingTokenTypeError()

import oauthlib
oauthlib.oauth2.rfc6749.parameters.validate_token_parameters = _monkeypatch_validate_token_parameters

class GoogleAPI(OAuth2API):
    id = 'google'
    default_report = 'week'
    label = 'Google Analytics'
    description = 'Weekly email reports of your analyics.'

    config = {
        'auth_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'scope': [
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/analytics.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
        ],


        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }

    def query_user(self):
        fields = ','.join(['id', 'kind', 'displayName', 'emails', 'name'])
        r = self.session.get('https://www.googleapis.com/oauth2/v1/userinfo', params=fields)
        r.raise_for_status()

        user_info = r.json()
        remote_id = user_info['id']
        email = user_info.get('email')
        name = user_info.get('name')

        return remote_id, email, name, user_info


    def create_query(self, cache_keys):
        if self.request.features.get('offline'):
            from briefmetrics.test.fixtures.api_google import FakeQuery
            return FakeQuery(self, cache_keys=cache_keys)

        return Query(self, cache_keys=cache_keys)


    @staticmethod
    def inject_transaction(tracking_id, t, pretend=False):
        if not t:
            return

        collect_fn = pretend_collect if pretend else collect

        items = t.pop('items', [])
        collect_fn(tracking_id, **t)
        for item in items:
            collect_fn(tracking_id, **item)


class Query(object):
    def __init__(self, oauth, cache_keys):
        self.oauth = oauth
        self.api = oauth.session
        self.cache_keys = cache_keys

    @ReportRegion.cache_on_arguments()
    def _get(self, url, params=None, _cache_keys=None):
        r = self.api.get(url, params=params)
        assert_response(r)
        return r.json()

    def _get_data(self, params=None, _cache_keys=None):
        return self._get('https://www.googleapis.com/analytics/v3/data/ga', params=params, _cache_keys=_cache_keys or self.cache_keys)

    def _columns_to_params(self, params, dimensions=None, metrics=None):
        columns = []
        if dimensions:
            params['dimensions'] = ','.join(col.id for col in dimensions)
            columns += dimensions

        if metrics:
            params['metrics'] = ','.join(col.id for col in metrics)
            columns += metrics

        return columns

    def get(self, url, params=None):
        return self._get(url, params=params, _cache_keys=self.cache_keys)

    def get_table(self, params, dimensions=None, metrics=None, renew=False, _cache_keys=None):
        params = dict(params)
        columns = self._columns_to_params(params, dimensions=dimensions, metrics=metrics)

        t = Table(columns)
        if renew:
            t = t.new()
        t._response_data = response_data = self._get_data(params)
        if 'rows' not in response_data:
            return t

        for row in response_data['rows']:
            t.add(row)

        return t

    def get_profile(self, remote_id=None):
        r = self.get_profiles()
        if remote_id is None:
            return next(iter(r), None)

        return next((item for item in r if item['id'] == remote_id), None)

    def get_properties(self):
        # Note: Not used
        try:
            r = self.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties')
        except InvalidGrantError:
            raise APIError('Insufficient permissions to query Google Analytics. Please re-connect your account.')
        items = r.get('items')
        if not items:
            return {}
        return dict((item['id'], item.get('name', '(Unnamed)')) for item in items)

    def get_profiles(self):
        try:
            r = self.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles')
        except InvalidGrantError:
            raise APIError('Insufficient permissions to query Google Analytics. Please re-connect your account.')
        profiles = r.get('items') or []
        if not profiles:
            return profiles

        properties = self.get_properties()
        for profile in profiles:
            profile['displayName'] = properties.get(profile['webPropertyId']) or ''
            u = h.human_url(profile.get('websiteUrl'))
            if u in ('--', '-'):
                u = profile.get('displayName', '(Unknown App)')
            profile['humanUrl'] = u

        return profiles
