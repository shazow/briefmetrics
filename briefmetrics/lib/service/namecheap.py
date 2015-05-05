from .base import Service

from briefmetrics.lib.http import assert_response
from unstdlib import random_string
from requests import Session
from requests_hawk import HawkAuth
from urllib import quote


class NamecheapAPI(Service):
    """
    from briefmetrics.lib import service
    nc = service.registry['namecheap'](request)
    prefix = 'https://api.sandbox.partners.namecheap.com'

    # Create fake event
    r = nc.request('POST', '/v1/saas/saas/subscription/mock')
    data = r.json()
    token = data['event']['event_token']

    # Get event details
    r = nc.request('GET', '/v1/saas/saas/event/%s' % token)
    data = r.json()
    return_uri = data['event']['returnURI']
    subscription_id = data['event']['subscription_id']

    ''' data ->
    {
        "type": "subscription_create",
        "event": {
            "returnURI": "https://api.sandbox.partners.namecheap.com/v1/saas/saas/eventResponse/67e2b7f7dcad46cfa4e2013f224fcead",
            "id": "b17055ca229140309e0a54df7804fb85",
            "user": {
                "username": "testuser"
            },
            "subscription_id": "308",
            "configuration": {},
            "order": {
                "product_id": 17
            }
        }
    }
    '''

    # Acknowledge event, activate subscription
    ack = {
        'type': 'subscription_create_resp',
        'id': data['event']['id'],
        'response': {
            'state': 'Active',
            'provider_id': nc.config['client_id'],
        }
    }
    r = nc.session.request('PUT', return_uri, json=ack)

    # Create invoice
    r = nc.session.request('POST', prefix + '/v1/billing/invoice', data={
        'subscription_id': subscription_id,
    })
    data = r.json()
    invoice_id = data['result']['id']

    # Get invoice
    # /v1/billing/invoice/{invoice_id}
    r = nc.session.request('GET', prefix + '/v1/billing/invoice/{invoice_id}'.format(invoice_id=invoice_id))

    # Add line item
    item = {
        'description' : "Briefmetrics: 1 year of Starter plan",
        'amount': 72,
        'taxable': 0,
    }
    r = nc.session.request('POST', prefix + '/v1/billing/invoice/%s/line_items' % invoice_id, json=item)

    # Add payment
    # POST /v1/billing/invoice/{invoice_id}/payments
    payment = {
        'description': item['description'],
    }
    r = nc.session.request('POST', prefix + '/v1/billing/invoice/{invoice_id}/payments'.format(invoice_id=invoice_id), json=payment)
    data = r.json()
    payment_id = data['result']['id']

    # Get payment info
    r = nc.session.request('GET', prefix + '/v1/payments/{payment_id}'.format(payment_id=payment_id))

    """
    id = 'namecheap'
    url_prefix = 'https://api.partners.namecheap.com'
    protocol = 'openidconnect'

    config = {
        'auth_url': 'https://www.namecheap.com/apps/sso/authorize',
        'scope': ['openid', 'namecheap'],

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
        # 'sso_client_id': ...,
    }
    instance = None # Replaced during init

    def __init__(self, request=None):
        self._request = request
        self.session = Session()
        self.session.auth = HawkAuth(credentials={
            'id': self.config['client_id'],
            'key': self.config['client_secret'],
            'algorithm': 'sha256',
        })
        self.url_prefix = self.config.get('api_url', self.url_prefix)

    def request(self, method, resource, **kw):
        r = self.session.request(method, self.url_prefix+resource, **kw)
        assert_response(r)
        return r

    def auth_url(self, **extra_kw):
        params = {
            'response_type': 'id_token token',
            'client_id': self.config['sso_client_id'],
            'scope': ' '.join(self.config['scope']),
            'redirect_uri': self._request.route_url('account_connect', service=self.id),
            'nonce': random_string(6),
        }
        if extra_kw:
            params.update(extra_kw)

        # Can't use urllib.urlencode because %20 instead of +.
        encoded = '&'.join('='.join((k, quote(v, safe=''))) for k, v in params.iteritems())
        url = self.config['auth_url'] + '?' + encoded
        return url, params.get('state')

    # http%3A%2F%2Flocalhost%3A5000%2Faccount%2Fconnect%2Fnamecheap
    # http%3A%2F%2Flocalhost%3A5000%2Faccount%2Fconnect%2Fnamecheap
