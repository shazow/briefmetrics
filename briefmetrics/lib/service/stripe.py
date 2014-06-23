import time
import datetime

from .base import OAuth2API

from briefmetrics.lib import helpers as h
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.report import Report, EmptyReportError, WeeklyMixin, sparse_cumulative
from briefmetrics.lib.table import Column, Table
from briefmetrics.lib.gcharts import encode_rows


def to_epoch(dt):
    return int(time.mktime(dt.timetuple()))

def to_datetime(n):
    return datetime.datetime.utcfromtimestamp(n)

def to_email(name, email):
    if not name:
        return email

    return u'"{name}" &lt;{email}&gt;'.format(
        name=name.replace('"', '&#34;'),
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
        last_month_date_start = self.date_end - datetime.timedelta(days=self.date_end.day)
        last_month_date_start -= datetime.timedelta(days=last_month_date_start.day - 1)

        # TODO: Check 'has_more'
        week_params = {
            'created[gte]': to_epoch(self.date_start),
            'created[lt]': to_epoch(self.date_end + datetime.timedelta(days=1)),
            'limit': 100,
        }

        self.tables['customers'] = customers_table = Table([
            Column('id'),
            Column('created', label='', visible=0, type_format=lambda d: str(d.date())),
            Column('email', label='New Customers', visible=3),
            Column('plan', label='', visible=2, nullable=True),
            Column('amount', label='', visible=1, type_class='number', nullable=True),
        ])

        r = api_query.get('https://api.stripe.com/v1/customers', params=week_params)

        for item in r.get('data', []):
            plan = (item.get('subscription') or {}).get('plan')
            plan_name, plan_amount = None, None

            if plan:
                plan_name = plan['name'][len('Briefmetrics: '):]
                interval = {'month': 'mo', 'year': 'yr'}.get(plan['interval'], plan['interval'])
                plan_amount = u'{amount}/{interval}'.format(amount=h.human_dollar(plan['amount']), interval=interval)

            customers_table.add([
                item['id'],
                to_datetime(item['created']),
                item['email'],
                plan_name or '(No plan yet)',
                plan_amount or '',
            ])

        ##

        self.tables['events'] = events_table = Table([
            Column('timestamp', label='', visible=0, type_format=lambda d: str(d.date())),
            Column('type', label='Events', visible=1),
            Column('content', label='', visible=2),
        ])

        r = api_query.get('https://api.stripe.com/v1/events', params=week_params)
        for item in r.get('data', []):
            events_table.add([
                to_datetime(item['created']),
                item['type'],
                item['data']['object'].get('description'),
            ])

        ##

        historic_table = Table([
            Column('created', visible=0),
            Column('amount', label='Amount', visible=1),
        ])

        r = api_query.get('https://api.stripe.com/v1/charges', params={
            'created[gte]': to_epoch(last_month_date_start),
            'created[lt]': to_epoch(self.date_end + datetime.timedelta(days=1)),
            'limit': 100,
        })
        for item in r.get('data', []):
            historic_table.add([
                to_datetime(item['created']),
                item['amount'],
            ])

        iter_historic = historic_table.iter_visible(reverse=True)
        _, views_column = next(iter_historic)
        monthly_data, max_value = sparse_cumulative(iter_historic)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = u'${:0.2f} dollar'
        self.data['total_current'] = current_month[-1]/100.0
        self.data['total_last'] = last_month[-1]/100.0
        self.data['total_last_relative'] = last_month[min(len(current_month), len(last_month))-1]/100.0
        self.data['total_last_date_start'] = last_month_date_start

