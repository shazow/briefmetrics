from .base import Service

from briefmetrics.lib.http import assert_response

import requests
from requests_hawk import HawkAuth
from urllib import urlencode
from unstdlib import random_string


class NamecheapAPI(Service):
    """
    from briefmetrics.lib import service
    nc = service.registry['namecheap'](request)
    prefix = 'https://api.sandbox.partners.namecheap.com'

    # Create fake event
    r = nc.session.request('POST', prefix + '/v1/saas/saas/subscription/mock')
    data = r.json()
    token = data['event']['event_token']

    # Get event details
    r = nc.session.request('GET', prefix + '/v1/saas/saas/event/%s' % token)
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
    # XXX: Not working?
    r = nc.session.request('GET', prefix + '/v1/payments/{payment_id}'.format(payment_id=payment_id))

    """
    id = 'namecheap'
    url_prefix = 'https://api.sandbox.partners.namecheap.com'

    config = {
        'auth_url': 'http://www.sandbox.namecheap.com/apps/sso/authorize', # TODO: Replace with https://www.namecheap.com/apps/sso/authorize
        'token_url': 'XXX',
        'scope': ['read_only'],

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }
    instance = None # Replaced during init

    def __init__(self, request, token=None, state=None):
        self.request = request
        self.token = token
        self.state = state

        self.session = requests.Session()
        self.session.auth = HawkAuth(credentials={
            'id': self.config['client_id'],
            'key': self.config['client_secret'],
            'algorithm': 'sha256',
        })

    def request(self, method, resource, **kw):
        r = self.session.request(method, self.url_prefix+resource, **kw)
        assert_response(r)
        return r

    def auth_url(self, **extra_kw):
        params = {
            'response_type': 'id_token token',
            'client_id': self.config['client_id'],
            'redirect_uri': self.request.route_url('account_connect', service=self.id),
            'nonce': random_string(8),
        }
        if extra_kw:
            params.update(extra_kw)

        return self.config['auth_url'] + '?' + urlencode(params), extra_kw.get('state')

    def auth_token(self, response_url):
        # XXX: Do nothing? :/
        return
