import time
import datetime

from .base import OAuth2API

from briefmetrics.lib import helpers as h
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.report import Report, WeeklyMixin, sparse_cumulative
from briefmetrics.lib.table import Column, Table, Timeline
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

    def query_user(self):
        r = self.session.get('https://api.stripe.com/v1/account')
        r.raise_for_status()
        user_info = r.json()
        return user_info['email'], user_info.get('display_name')

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

    def get_paged(self, url, params=None):
        data = []
        starting_after = None
        while True:
            if starting_after:
                params['starting_after'] = starting_after

            r = self.get(url, params)
            items = r['data']
            data += items
            if not r.get('has_more'):
                return data

            starting_after = items[-1]['id']

    def get_profile(self, remote_id=None):
        r = self.get('https://api.stripe.com/v1/account')
        if remote_id and r['id'] != remote_id:
            return

        return r

    def get_profiles(self):
        p = self.get_profile()
        if not p:
            return
        return [p]


event_formatters = {
    'transfer': 'Transfer of {amount_str} is {status}.',
    'balance': 'Balance available: {available}',
    'charge': 'Charge {type}: {amount_str} for {email}',
    'customer': 'Customer {type}: {email}',
    'customer.subscription': 'Customer subscription {type}: {plan}',
    'customer.card': 'Customer card {type}: {customer}',
}

def describe_plan(plan):
    interval = {'month': 'mo', 'year': 'yr'}.get(plan['interval'], plan['interval'])
    return u'"{name}" at {amount}/{interval}'.format(name=plan['name'], amount=h.human_dollar(plan['amount']), interval=interval)


def describe_event(item):
    type_full = item['type']
    type_prefix, type_suffix = type_full.rsplit('.', 1)

    if type_prefix in ['invoice'] or type_full in ['customer.subscription.updated']:
        # Skip
        return

    f = event_formatters.get(type_full) or event_formatters.get(type_prefix)
    obj = item['data']['object']

    if type_prefix == 'transfer':
        r = f.format(amount_str=h.human_dollar(obj['amount'], currency=obj['currency']), status=obj['status'])
        if type_full == 'transfer.paid':
            r = '<b>%s</b>' % r
        return r

    elif type_prefix == 'balance':
        available = ', '.join((h.human_dollar(a['amount'], currency=a['currency'])) for a in obj['available'])
        pending = ', '.join((h.human_dollar(a['amount'], currency=a['currency'])) for a in obj['pending'])
        r = f.format(available=available)
        if pending:
            r += ' (also %s pending)' % pending

        return r

    elif type_prefix == 'customer':
        r = f.format(type=type_suffix, email=obj.get('email') or '(no email)')
        if type_full in ('customer.created', 'customer.deleted'):
            r = '<b>%s</b>' % r
        return r

    elif type_prefix == 'customer.subscription':
        return f.format(type=type_suffix, plan=describe_plan(obj['plan']))

    elif type_prefix == 'customer.card':
        return f.format(type=type_suffix, customer=obj['customer'])

    elif type_prefix == 'charge':
        amount_str = h.human_dollar(obj['amount'], currency=obj['currency'])
        r = f.format(type=type_suffix, amount_str=amount_str, email=obj['receipt_email'])
        return '<b>%s</b>' % r

    if not f:
        return ' '.join([type_full, obj.get('description') or ''])

    return f.format(**obj)



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

        self.tables['customers'] = customers_table = Timeline()

        items = api_query.get_paged('https://api.stripe.com/v1/customers', params=week_params)

        for item in items:
            plan = (item.get('subscription') or {}).get('plan')
            if plan:
                plan = describe_plan(plan)

            customers_table.add([
                to_datetime(item['created']),
                ' '.join([
                    item.get('email') or '(no email)',
                    plan or '(no plan yet)',
                ])
            ])

        ##

        self.tables['events'] = events_table = Timeline()

        items = api_query.get_paged('https://api.stripe.com/v1/events', params=week_params)
        for item in items:
            events_table.add([
                to_datetime(item['created']),
                describe_event(item),
            ])

        ##

        historic_table = Table([
            Column('created', visible=0),
            Column('amount', label='Amount', visible=1),
        ])

        items = api_query.get_paged('https://api.stripe.com/v1/charges', params={
            'created[gte]': to_epoch(last_month_date_start),
            'created[lt]': to_epoch(self.date_end + datetime.timedelta(days=1)),
            'limit': 100,
        })
        for item in items:
            if not item['paid'] or item['refunded']:
                continue
            historic_table.add([
                to_datetime(item['created']),
                item['amount'],
            ])

        iter_historic = historic_table.iter_visible(reverse=True)
        _, views_column = next(iter_historic)
        monthly_data, max_value = sparse_cumulative(iter_historic, final_date=self.date_end)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[min(len(current_month), len(last_month))-1]
        self.data['total_last_date_start'] = last_month_date_start
