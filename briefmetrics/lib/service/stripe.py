import time
import datetime

from .base import OAuth2API

from briefmetrics.lib.http import assert_response
from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.report import Report, EmptyReportError, WeeklyMixin
from briefmetrics.lib.table import Column, Table


def to_epoch(dt):
    return time.mktime(dt.timetuple())

def to_datetime(n):
    return datetime.datetime.utcfromtimestamp(n)

def to_email(name, email):
    if not name:
        return email

    return u'"{name}" <{email}>'.format(
        display_name=name.replace('"', '&#34;'),
        email=email,
    )


class StripeAPI(OAuth2API):
    id = 'stripe'
    default_report = 'stripe'
    is_autocreate = True

    config = {
        'auth_url': 'https://connect.stripe.com/oauth/authorize',
        'token_url': 'https://connect.stripe.com/oauth/token',
        'scope': ['read_only'],

        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }

    def create_query(self, cache_keys=None):
        return Query(self, cache_keys=cache_keys)


class Query(object):
    def __init__(self, oauth, cache_keys=None):
        self.oauth = oauth
        self.api = oauth.session
        self.cache_keys = None

    @ReportRegion.cache_on_arguments()
    def _get(self, url, params=None, _cache_keys=None):
        r = self.api.get(url, params=params)
        assert_response(r)
        return r.json()

    def get(self, url, params=None):
        return self._get(url, params=params, _cache_keys=self.cache_keys)

    def get_profile(self, remote_id=None):
        r = self.get('https://api.stripe.com/v1/account')
        if remote_id and r['id'] != remote_id:
            return

        return r




class StripeReport(WeeklyMixin, Report):
    id = 'stripe'
    label = 'Stripe'

    template = 'email/report/stripe.mako'

    def fetch(self, api_query):
        new_customers = Table([
            Column('id'),
            Column('created'),
            Column('email_to'),
            Column('plan'),
        ])

        r = api_query.get('https://api.stripe.com/v1/customers', params={
            'created[gte]': to_epoch(self.date_start),
            'created[lt]': to_epoch(self.date_end + datetime.timedelta(days=1)),
        })

        for customer in r.get('data', {}):
            plan = customer.get('subscription', {}).get('plan', {})
            if plan:
                plan = '{name} @ ${amount}/{interval}'.format(**plan)

            new_customers.add([
                customer['id'],
                to_datetime(customer['created']),
                to_email(name=customer['description'], email=customer['email']),
                plan,
            ])
