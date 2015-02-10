import datetime
import uuid
import requests
from urllib import urlencode
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from briefmetrics.lib import helpers as h
from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.gcharts import encode_rows
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.report import Report, EmptyReportError, MonthlyMixin, WeeklyMixin, DailyMixin, inject_table_delta, cumulative_by_month
from briefmetrics.lib.table import Table, Column
from briefmetrics.lib.exceptions import APIError

from .base import OAuth2API

def to_display_name(remote_data):
    return h.human_url(remote_data.get('websiteUrl')) or remote_data.get('display_name') or remote_data.get('name')


class GoogleAPI(OAuth2API):
    id = 'google'
    default_report = 'week'
    label = 'Google Analytics'
    description = 'Weekly email reports of your analyics.'

    config = {
        'auth_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'scope': [
            'profile',
            'email',
            'https://www.googleapis.com/auth/analytics.readonly',
        ],


        # Populate these during init:
        # 'client_id': ...,
        # 'client_secret': ...,
    }

    def query_user(self):
        fields = ','.join(['id', 'kind', 'displayName', 'emails', 'name'])
        r = self.session.get('https://www.googleapis.com/plus/v1/people/me', params=fields)
        r.raise_for_status()

        user_info = r.json()
        for e in user_info['emails']:
            # Find the account email if there is one.
            if e['type'] == 'account':
                break

        remote_id = user_info['id']
        email = e['value']
        name = user_info.get('displayName')

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



"""
METRICS = [u'ga:CPC', u'ga:CPM', u'ga:CTR', u'ga:ROI', u'ga:RPC', u'ga:adClicks', u'ga:adCost', u'ga:adsenseAdUnitsViewed', u'ga:adsenseAdsClicks', u'ga:adsenseAdsViewed', u'ga:adsenseCTR', u'ga:adsenseECPM', u'ga:adsenseExits', u'ga:adsensePageImpressions', u'ga:adsenseRevenue', u'ga:appviews', u'ga:appviewsPerVisit', u'ga:avgDomContentLoadedTime', u'ga:avgDomInteractiveTime', u'ga:avgDomainLookupTime', u'ga:avgEventValue', u'ga:avgPageDownloadTime', u'ga:avgPageLoadTime', u'ga:avgRedirectionTime', u'ga:avgScreenviewDuration', u'ga:avgSearchDepth', u'ga:avgSearchDuration', u'ga:avgSearchResultViews', u'ga:avgServerConnectionTime', u'ga:avgServerResponseTime', u'ga:avgTimeOnPage', u'ga:avgTimeOnSite', u'ga:avgUserTimingValue', u'ga:bounces', u'ga:costPerConversion', u'ga:costPerGoalConversion', u'ga:costPerTransaction', u'ga:domContentLoadedTime', u'ga:domInteractiveTime', u'ga:domLatencyMetricsSample', u'ga:domainLookupTime', u'ga:entranceBounceRate', u'ga:entranceRate', u'ga:entrances', u'ga:eventValue', u'ga:eventsPerVisitWithEvent', u'ga:exceptions', u'ga:exceptionsPerScreenview', u'ga:exitRate', u'ga:exits', u'ga:fatalExceptions', u'ga:fatalExceptionsPerScreenview', u'ga:goalAbandonRateAll', u'ga:goalAbandonsAll', u'ga:goalCompletionsAll', u'ga:goalConversionRateAll', u'ga:goalStartsAll', u'ga:goalValueAll', u'ga:goalValueAllPerSearch', u'ga:goalValuePerVisit', u'ga:goalXXAbandonRate', u'ga:goalXXAbandons', u'ga:goalXXCompletions', u'ga:goalXXConversionRate', u'ga:goalXXStarts', u'ga:goalXXValue', u'ga:impressions', u'ga:itemQuantity', u'ga:itemRevenue', u'ga:itemsPerPurchase', u'ga:localItemRevenue', u'ga:localTransactionRevenue', u'ga:localTransactionShipping', u'ga:localTransactionTax', u'ga:margin', u'ga:metricXX', u'ga:newVisits', u'ga:organicSearches', u'ga:pageDownloadTime', u'ga:pageLoadSample', u'ga:pageLoadTime', u'ga:pageValue', u'ga:pageviews', u'ga:pageviewsPerVisit', u'ga:percentNewVisits', u'ga:percentSearchRefinements', u'ga:percentVisitsWithSearch', u'ga:redirectionTime', u'ga:revenuePerItem', u'ga:revenuePerTransaction', u'ga:screenviews', u'ga:screenviewsPerSession', u'ga:searchDepth', u'ga:searchDuration', u'ga:searchExitRate', u'ga:searchExits', u'ga:searchGoalConversionRateAll', u'ga:searchGoalXXConversionRate', u'ga:searchRefinements', u'ga:searchResultViews', u'ga:searchUniques', u'ga:searchVisits', u'ga:serverConnectionTime', u'ga:serverResponseTime', u'ga:socialActivities', u'ga:socialInteractions', u'ga:socialInteractionsPerVisit', u'ga:speedMetricsSample', u'ga:timeOnPage', u'ga:timeOnScreen', u'ga:timeOnSite', u'ga:totalEvents', u'ga:totalValue', u'ga:transactionRevenue', u'ga:transactionRevenuePerVisit', u'ga:transactionShipping', u'ga:transactionTax', u'ga:transactions', u'ga:transactionsPerVisit', u'ga:uniqueAppviews', u'ga:uniqueEvents', u'ga:uniquePageviews', u'ga:uniquePurchases', u'ga:uniqueScreenviews', u'ga:uniqueSocialInteractions', u'ga:userTimingSample', u'ga:userTimingValue', u'ga:visitBounceRate', u'ga:visitors', u'ga:visits', u'ga:visitsWithEvent']
DIMENSIONS = [u'ga:adContent', u'ga:adDestinationUrl', u'ga:adDisplayUrl', u'ga:adDistributionNetwork', u'ga:adFormat', u'ga:adGroup', u'ga:adKeywordMatchType', u'ga:adMatchType', u'ga:adMatchedQuery', u'ga:adPlacementDomain', u'ga:adPlacementUrl', u'ga:adSlot', u'ga:adSlotPosition', u'ga:adTargetingOption', u'ga:adTargetingType', u'ga:adwordsAdGroupID', u'ga:adwordsCampaignID', u'ga:adwordsCreativeID', u'ga:adwordsCriteriaID', u'ga:adwordsCustomerID', u'ga:affiliation', u'ga:appId', u'ga:appInstallerId', u'ga:appName', u'ga:appVersion', u'ga:browser', u'ga:browserVersion', u'ga:campaign', u'ga:city', u'ga:continent', u'ga:country', u'ga:currencyCode', u'ga:customVarNameXX', u'ga:customVarValueXX', u'ga:date', u'ga:dateHour', u'ga:day', u'ga:dayOfWeek', u'ga:dayOfWeekName', u'ga:daysSinceLastVisit', u'ga:daysToTransaction', u'ga:deviceCategory', u'ga:dimensionXX', u'ga:eventAction', u'ga:eventCategory', u'ga:eventLabel', u'ga:exceptionDescription', u'ga:exitPagePath', u'ga:exitScreenName', u'ga:experimentId', u'ga:experimentVariant', u'ga:flashVersion', u'ga:fullReferrer', u'ga:goalCompletionLocation', u'ga:goalPreviousStep1', u'ga:goalPreviousStep2', u'ga:goalPreviousStep3', u'ga:hasSocialSourceReferral', u'ga:hostname', u'ga:hour', u'ga:interestAffinityCategory', u'ga:interestInMarketCategory', u'ga:interestOtherCategory', u'ga:isMobile', u'ga:isTablet', u'ga:isoWeek', u'ga:isoYear', u'ga:isoYearIsoWeek', u'ga:javaEnabled', u'ga:keyword', u'ga:landingPagePath', u'ga:landingScreenName', u'ga:language', u'ga:latitude', u'ga:longitude', u'ga:medium', u'ga:metro', u'ga:minute', u'ga:mobileDeviceBranding', u'ga:mobileDeviceInfo', u'ga:mobileDeviceMarketingName', u'ga:mobileDeviceModel', u'ga:mobileInputSelector', u'ga:month', u'ga:networkDomain', u'ga:networkLocation', u'ga:nextPagePath', u'ga:nthDay', u'ga:nthMinute', u'ga:nthMonth', u'ga:nthWeek', u'ga:operatingSystem', u'ga:operatingSystemVersion', u'ga:pageDepth', u'ga:pagePath', u'ga:pagePathLevel1', u'ga:pagePathLevel2', u'ga:pagePathLevel3', u'ga:pagePathLevel4', u'ga:pageTitle', u'ga:previousPagePath', u'ga:productCategory', u'ga:productName', u'ga:productSku', u'ga:referralPath', u'ga:region', u'ga:screenColors', u'ga:screenDepth', u'ga:screenName', u'ga:screenResolution', u'ga:searchCategory', u'ga:searchDestinationPage', u'ga:searchKeyword', u'ga:searchKeywordRefinement', u'ga:searchStartPage', u'ga:searchUsed', u'ga:secondPagePath', u'ga:socialActivityAction', u'ga:socialActivityContentUrl', u'ga:socialActivityDisplayName', u'ga:socialActivityEndorsingUrl', u'ga:socialActivityNetworkAction', u'ga:socialActivityPost', u'ga:socialActivityTagsSummary', u'ga:socialActivityTimestamp', u'ga:socialActivityUserHandle', u'ga:socialActivityUserPhotoUrl', u'ga:socialActivityUserProfileUrl', u'ga:socialEngagementType', u'ga:socialInteractionAction', u'ga:socialInteractionNetwork', u'ga:socialInteractionNetworkAction', u'ga:socialInteractionTarget', u'ga:socialNetwork', u'ga:source', u'ga:sourceMedium', u'ga:subContinent', u'ga:transactionId', u'ga:userDefinedValue', u'ga:userTimingCategory', u'ga:userTimingLabel', u'ga:userTimingVariable', u'ga:visitCount', u'ga:visitLength', u'ga:visitorAgeBracket', u'ga:visitorGender', u'ga:visitorType', u'ga:visitsToTransaction', u'ga:week', u'ga:year', u'ga:yearMonth', u'ga:yearWeek',]

# Generated with:
#   import json
#   r = json.load(open('docs/ga-columns.json'))
#   dimensions = sorted(i['id'] for i in r['items'] if i['attributes'][u'type'] == u'DIMENSION')
#   metrics = sorted(i['id'] for i in r['items'] if i['attributes'][u'type'] == u'METRIC')
"""


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

    def get_table(self, params, dimensions=None, metrics=None, _cache_keys=None):
        params = dict(params)
        columns = self._columns_to_params(params, dimensions=dimensions, metrics=metrics)

        t = Table(columns)
        t._response_data = response_data = self._get_data(params)
        if 'rows' not in response_data:
            return t

        for row in response_data['rows']:
            t.add(row)

        return t

    def get_profile(self, remote_id=None):
        r = self.get_profiles()
        if remote_id is None:
            return next(iter(r, None))

        return next((item for item in r if item['id'] == remote_id), None)

    def get_profiles(self):
        # account_id used for caching, not in query.
        try:
            r = self.get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles')
        except InvalidGrantError:
            raise APIError('Insufficient permissions to query Google Analytics. Please re-connect your account.')
        return r.get('items') or []


COLLECT_URL = 'https://ssl.google-analytics.com/collect'
COLLECT_SESSION = requests.Session()


def pretend_collect(*args, **kw):
    print "pretend_collect:", args, kw


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



## Reports:


def _prune_abstract(v):
    if v.startswith('('):
        return
    return v

def _prune_referrer(v):
    if v.startswith('('):
        return
    if v.startswith('semalt.semalt.com'):
        return
    return v

def _cast_percent(v):
    return float(v or 0.0)

def _format_percent(f):
    return h.human_percent(f, denominator=100.0)

def _cast_time(v):
    v = float(v or 0.0)
    if v:
        return v

def _cast_title(v):
    # Also prunes abstract
    if not v or v.startswith('('):
        return

    if not v[0].isupper():
        return v.title()

    return v



# TODO: Rename ids to GA-specific

class GAReport(Report):
    def __init__(self, report, since_time, remote_data=None, display_name=None):
        super(GAReport, self).__init__(report, since_time)
        if remote_data:
            self.remote_id = str(remote_data.get('id', self.remote_id))

        self.remote_data = remote_data = remote_data or self.report.remote_data or {}
        self.display_name = display_name or report.display_name

        base_url = remote_data.get('websiteUrl', '')
        if base_url and 'http://' not in base_url:
            base_url = 'http://' + base_url

        self.base_url = remote_data.get('websiteUrl', '')


class ActivityReport(WeeklyMixin, GAReport):
    id = 'week'
    label = 'Weekly'

    template = 'email/report/weekly.mako'

    def get_preview(self):
        if len(self.tables['summary'].rows) < 2:
            return u''

        primary_metric = self.report.config.get('intro') or 'ga:pageviews'
        this_week, last_week = (r.get(primary_metric) for r in self.tables['summary'].rows[:2])
        delta = (this_week / float(last_week or 1.0)) - 1
        return u"Your site had {this_week} this {interval} ({delta} over last {interval}).".format(
            this_week=h.format_int(this_week, self.data['total_units']),
            delta=h.human_percent(delta, signed=True),
            interval=self.data.get('interval_label', 'week'),
        )

    def _get_social_search(self, google_query, date_start, date_end, summary_metrics, max_results=10):
        organic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start,
                'end-date': date_end,
                'filters': 'ga:medium==organic;ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': str(max_results),
            },
            dimensions=[
                Column('ga:source', type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        social_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': date_start,
                'end-date': date_end,
                'sort': '-ga:pageviews',
                'max-results': str(max_results),
            },
            dimensions=[
                Column('ga:socialNetwork', type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        t = Table(columns=[
            Column('source', label='Social & Search', visible=1, type_cast=_cast_title),
        ] + [col.new() for col in summary_metrics])

        for cells in social_table.iter_rows():
            t.add(cells)

        for cells in organic_table.iter_rows():
            t.add(cells)

        t.sort(reverse=True)
        return t

    def _get_goals(self, google_query, interval_field):
        goals_api = 'https://www.googleapis.com/analytics/v3/management/accounts/{accountId}/webproperties/{webPropertyId}/profiles/{profileId}/goals'
        r = google_query.get(goals_api.format(profileId=self.remote_data['id'], **self.remote_data))
        has_goals = r.get('items') or []
        metrics = [
                Column('ga:goal{id}ConversionRate'.format(id=g['id']), label=g['name'], type_cast=float) for g in has_goals if g.get('active')
        ]

        if not metrics:
            return

        raw_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start, # Extra week
                'end-date': self.date_end,
                'sort': '-{}'.format(interval_field),
            },
            metrics=metrics[-10:],
            dimensions=[
                Column(interval_field),
            ],
        )

        if len(raw_table.rows) != 2:
            return

        t = Table(columns=[
            Column('goal', label='Goals', visible=1, type_cast=_cast_title),
            Column('completions', label='Converts', visible=0, type_cast=_cast_percent, type_format=_format_percent, threshold=0),
        ])

        this_week, last_week = raw_table.rows
        col_compare = t.columns[1]
        col_compare_delta = Column('%s:delta' % col_compare.id, label='Conversions', type_cast=float, type_format=h.human_delta, threshold=0)
        has_completions = False
        for col_id, pos in raw_table.column_to_index.items():
            col = raw_table.columns[pos]
            if not col.id.startswith('ga:goal'):
                continue

            completions, completions_last = this_week.values[pos], last_week.values[pos]
            row = t.add([col.label, completions])

            if completions > 0.1:
                has_completions = True
                delta = (completions - completions_last) / 100.0 # / float(completions)
                if abs(delta) > 0.01:
                    row.tag(type='delta', value=h.human_percent(delta, signed=True), column=col_compare_delta, is_prefixed=True, is_positive=delta>0)

        if not has_completions:
            return

        t.sort(reverse=True)

        return t


    def fetch(self, google_query):
        last_month_date_start = self.date_end - datetime.timedelta(days=self.date_end.day)
        last_month_date_start -= datetime.timedelta(days=last_month_date_start.day - 1)

        interval_field = 'ga:nthWeek'
        if (self.date_end - self.date_start).days > 6:
            interval_field = 'ga:nthMonth'

        # Summary
        summary_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:visitors', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgTimeOnSite', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            Column('ga:visitBounceRate', label='Bounce Rate', type_cast=_cast_percent, type_format=_format_percent, reverse=True, threshold=0),
            Column('ga:goalConversionRateAll', label='Conversion', type_cast=float, type_format=_format_percent, threshold=0.1)
        ]
        self.tables['summary'] = summary_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start, # Extra week
                'end-date': self.date_end,
                'sort': '-{}'.format(interval_field),
            },
            dimensions=[
                Column(interval_field),
            ],
            metrics=summary_metrics + [Column('ga:visits', type_cast=int)],
        )

        has_pageviews = any(next(row) for row in summary_table.iter_rows('ga:pageviews'))
        if not has_pageviews:
            raise EmptyReportError()

        # Pages
        self.tables['pages'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:pageviews',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:pagePath', label='Pages', visible=1, type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics[:-1]] + [
                Column('ga:avgPageLoadTime', label='Page Load', type_cast=float, type_format=h.human_time, reverse=True, threshold=0)
            ],
        )

        # Referrers

        current_referrers = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'filters': 'ga:medium==referral;ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': '25',
            },
            dimensions=[
                Column('ga:fullReferrer', label='Referrer', visible=1, type_cast=_prune_referrer)
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        last_referrers = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.previous_date_start,
                'end-date': self.previous_date_end,
                'filters': 'ga:medium==referral;ga:socialNetwork==(not set)',
                'sort': '-ga:pageviews',
                'max-results': '250',
            },
            dimensions=[
                Column('ga:fullReferrer', label='Referrer', visible=1, type_cast=_prune_referrer)
            ],
            metrics=[
                summary_table.get('ga:pageviews').new(),
            ],
        )
        inject_table_delta(current_referrers, last_referrers, join_column='ga:fullReferrer')

        self.tables['referrers'] = current_referrers

        # Goals?
        self.tables['goals'] = self._get_goals(google_query, interval_field)


        # Historic

        historic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': last_month_date_start,
                'end-date': self.date_end,
            },
            dimensions=[
                Column('ga:date'),
                Column('ga:month', visible=0),
            ],
            metrics=[
                Column('ga:pageviews', label='Views', type_cast=int, visible=1),
                Column('ga:visitors', label='Uniques', type_cast=int),
            ],
        )

        intro_config = self.report.config.get('intro')
        if intro_config:
            # For John Sheehan
            historic_table.set_visible('ga:month', intro_config)

        iter_historic = historic_table.iter_visible()
        _, views_column = next(iter_historic)
        monthly_data, max_value = cumulative_by_month(iter_historic)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['total_last_relative'] = last_month[min(len(current_month), len(last_month))-1]
        self.data['total_last_date_start'] = last_month_date_start

        social_search_table = self._get_social_search(google_query, self.date_start, self.date_end, summary_metrics, max_results=25)
        last_social_search = self._get_social_search(google_query, self.previous_date_start, self.previous_date_end, summary_metrics, max_results=100)
        inject_table_delta(social_search_table, last_social_search, join_column='source')

        self.tables['social_search'] = social_search_table

        self.tables['social_search'].tag_rows()
        self.tables['referrers'].tag_rows()
        self.tables['pages'].tag_rows()


class ActivityConcatReport(ActivityReport):
    id = 'week-concat'
    label = 'Weekly (Combined)'

    template = 'email/report/weekly-concat.mako'

    def __init__(self, report, since_time):
        super(ActivityConcatReport, self).__init__(report, since_time)

        remote_data = report.remote_data['combined']
        contexts = []
        for data in remote_data:
            contexts.append(ActivityReport(report, since_time, remote_data=data, display_name=to_display_name(data)))

        self.contexts = contexts
        self.data = True

    def fetch(self, google_query):
        for context in self.contexts:
            context.fetch(google_query)

    def build(self):
        for context in self.contexts:
            context.build()

    def get_preview(self):
        primary_metric = self.report.config.get('intro') or 'ga:pageviews'
        assert self.contexts, "ActivityConcatReport with no contexts"

        total_units, interval = None, None
        this_week, last_week = 0, 0
        for context in self.contexts:
            if not context.tables.get('summary') or len(context.tables['summary'].rows) < 2:
                continue

            a, b = (r.get(primary_metric) for r in context.tables['summary'].rows[:2])
            this_week += a
            last_week += b
            total_units = context.data.get('total_units', total_units)
            interval = context.data.get('interval_label', interval)

        assert ctx, 'Failed to find valid context: %r' % self.contexts

        delta = (this_week / float(last_week or 1.0)) - 1
        return u"Your {number} combined sites had {this_week} this {interval} ({delta} over last {interval}).".format(
            number=len(self.contexts),
            this_week=h.format_int(this_week, total_units),
            delta=h.human_percent(delta, signed=True),
            interval=interval or 'week',
        )



class ActivityMonthlyReport(MonthlyMixin, ActivityReport):
    "Monthly report"
    id = 'activity-month'

    def build(self):
        super(ActivityMonthlyReport, self).build()
        self.data['interval_label'] = 'month'


class DailyReport(DailyMixin, GAReport):
    id = 'day'
    label = 'Alerts (Daily)'

    template = 'email/report/daily.mako'

    def fetch(self, google_query):
        pass


class TrendsReport(MonthlyMixin, GAReport):
    "Monthly report"
    id = 'month'
    label = 'Trends (Monthly)'

    template = 'email/report/monthly.mako'

    def fetch(self, google_query):
        last_month_date_start = (self.date_start - datetime.timedelta(days=self.date_start.day + 1)).replace(day=1)

        # Summary
        summary_metrics = [
            Column('ga:pageviews', label='Views', type_cast=int, type_format=h.human_int, threshold=0, visible=0),
            Column('ga:visitors', label='Uniques', type_cast=int, type_format=h.human_int),
            Column('ga:avgTimeOnSite', label='Time On Site', type_cast=_cast_time, type_format=h.human_time, threshold=0),
            Column('ga:visitBounceRate', label='Bounce Rate', type_cast=_cast_percent, type_format=_format_percent, reverse=True, threshold=0),
        ]
        self.tables['summary'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': last_month_date_start, # Extra month
                'end-date': self.date_end,
                'sort': '-ga:month',
            },
            dimensions=[
                Column('ga:month'),
            ],
            metrics=summary_metrics + [Column('ga:visits', type_cast=int)],
        )

        self.tables['geo'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:visitors',
                'max-results': '10',
            },
            dimensions=[
                Column('ga:country', label='Country', visible=1, type_cast=_prune_abstract),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['device'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:visitors',
            },
            dimensions=[
                Column('ga:deviceCategory', label='Device', visible=1, type_cast=_cast_title),
            ],
            metrics=[col.new() for col in summary_metrics],
        )

        self.tables['browser'] = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': self.date_start,
                'end-date': self.date_end,
                'sort': '-ga:visitors',
            },
            dimensions=[
                Column('ga:browser', label='Browser', visible=1),
            ],
            metrics=[col.new() for col in summary_metrics] + [
                Column('ga:avgPageLoadTime', label='Load Time', type_cast=float),
            ],
        )

        self.tables['geo'].tag_rows()
        self.tables['device'].tag_rows()
        self.tables['browser'].tag_rows()


        # TODO: Add last year's month

        historic_table = google_query.get_table(
            params={
                'ids': 'ga:%s' % self.remote_id,
                'start-date': last_month_date_start,
                'end-date': self.date_end,
            },
            dimensions=[
                Column('ga:date'),
                Column('ga:month', visible=0),
            ],
            metrics=[
                Column('ga:pageviews', label='Views', type_cast=int, visible=1),
                Column('ga:visitors', label='Uniques', type_cast=int),
            ],
        )

        intro_config = self.report.config.get('intro')
        if intro_config:
            # For John Sheehan
            historic_table.set_visible('ga:month', intro_config)

        iter_historic = historic_table.iter_visible()
        _, views_column = next(iter_historic)
        monthly_data, max_value = cumulative_by_month(iter_historic)
        last_month, current_month = monthly_data

        self.data['historic_data'] = encode_rows(monthly_data, max_value)
        self.data['total_units'] = '{:,} %s' % views_column.label.lower().rstrip('s')
        self.data['total_current'] = current_month[-1]
        self.data['total_last'] = last_month[-1]
        self.data['current_month'] = self.date_start.strftime('%B')
        self.data['last_month'] = last_month_date_start.strftime('%B')
        self.data['current_month_days'] = self.date_end.day
        self.data['last_month_days'] = (self.date_start - datetime.timedelta(days=1)).day
