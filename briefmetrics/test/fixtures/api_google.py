"""
METRICS = [u'ga:CPC', u'ga:CPM', u'ga:CTR', u'ga:ROI', u'ga:RPC', u'ga:adClicks', u'ga:adCost', u'ga:adsenseAdUnitsViewed', u'ga:adsenseAdsClicks', u'ga:adsenseAdsViewed', u'ga:adsenseCTR', u'ga:adsenseECPM', u'ga:adsenseExits', u'ga:adsensePageImpressions', u'ga:adsenseRevenue', u'ga:appviews', u'ga:appviewsPerVisit', u'ga:avgDomContentLoadedTime', u'ga:avgDomInteractiveTime', u'ga:avgDomainLookupTime', u'ga:avgEventValue', u'ga:avgPageDownloadTime', u'ga:avgPageLoadTime', u'ga:avgRedirectionTime', u'ga:avgScreenviewDuration', u'ga:avgSearchDepth', u'ga:avgSearchDuration', u'ga:avgSearchResultViews', u'ga:avgServerConnectionTime', u'ga:avgServerResponseTime', u'ga:avgTimeOnPage', u'ga:avgSessionDuration', u'ga:avgUserTimingValue', u'ga:bounces', u'ga:costPerConversion', u'ga:costPerGoalConversion', u'ga:costPerTransaction', u'ga:domContentLoadedTime', u'ga:domInteractiveTime', u'ga:domLatencyMetricsSample', u'ga:domainLookupTime', u'ga:entranceBounceRate', u'ga:entranceRate', u'ga:entrances', u'ga:eventValue', u'ga:eventsPerVisitWithEvent', u'ga:exceptions', u'ga:exceptionsPerScreenview', u'ga:exitRate', u'ga:exits', u'ga:fatalExceptions', u'ga:fatalExceptionsPerScreenview', u'ga:goalAbandonRateAll', u'ga:goalAbandonsAll', u'ga:goalCompletionsAll', u'ga:goalConversionRateAll', u'ga:goalStartsAll', u'ga:goalValueAll', u'ga:goalValueAllPerSearch', u'ga:goalValuePerVisit', u'ga:goalXXAbandonRate', u'ga:goalXXAbandons', u'ga:goalXXCompletions', u'ga:goalXXConversionRate', u'ga:goalXXStarts', u'ga:goalXXValue', u'ga:impressions', u'ga:itemQuantity', u'ga:itemRevenue', u'ga:itemsPerPurchase', u'ga:localItemRevenue', u'ga:localTransactionRevenue', u'ga:localTransactionShipping', u'ga:localTransactionTax', u'ga:margin', u'ga:metricXX', u'ga:newVisits', u'ga:organicSearches', u'ga:pageDownloadTime', u'ga:pageLoadSample', u'ga:pageLoadTime', u'ga:pageValue', u'ga:pageviews', u'ga:pageviewsPerVisit', u'ga:percentNewVisits', u'ga:percentSearchRefinements', u'ga:percentVisitsWithSearch', u'ga:redirectionTime', u'ga:revenuePerItem', u'ga:revenuePerTransaction', u'ga:screenviews', u'ga:screenviewsPerSession', u'ga:searchDepth', u'ga:searchDuration', u'ga:searchExitRate', u'ga:searchExits', u'ga:searchGoalConversionRateAll', u'ga:searchGoalXXConversionRate', u'ga:searchRefinements', u'ga:searchResultViews', u'ga:searchUniques', u'ga:searchVisits', u'ga:serverConnectionTime', u'ga:serverResponseTime', u'ga:socialActivities', u'ga:socialInteractions', u'ga:socialInteractionsPerVisit', u'ga:speedMetricsSample', u'ga:timeOnPage', u'ga:timeOnScreen', u'ga:sessionDuration', u'ga:totalEvents', u'ga:totalValue', u'ga:transactionRevenue', u'ga:transactionRevenuePerVisit', u'ga:transactionShipping', u'ga:transactionTax', u'ga:transactions', u'ga:transactionsPerVisit', u'ga:uniqueAppviews', u'ga:uniqueEvents', u'ga:uniquePageviews', u'ga:uniquePurchases', u'ga:uniqueScreenviews', u'ga:uniqueSocialInteractions', u'ga:userTimingSample', u'ga:userTimingValue', u'ga:bounceRate', u'ga:users', u'ga:sessions', u'ga:sessionsWithEvent']
DIMENSIONS = [u'ga:adContent', u'ga:adDestinationUrl', u'ga:adDisplayUrl', u'ga:adDistributionNetwork', u'ga:adFormat', u'ga:adGroup', u'ga:adKeywordMatchType', u'ga:adMatchType', u'ga:adMatchedQuery', u'ga:adPlacementDomain', u'ga:adPlacementUrl', u'ga:adSlot', u'ga:adSlotPosition', u'ga:adTargetingOption', u'ga:adTargetingType', u'ga:adwordsAdGroupID', u'ga:adwordsCampaignID', u'ga:adwordsCreativeID', u'ga:adwordsCriteriaID', u'ga:adwordsCustomerID', u'ga:affiliation', u'ga:appId', u'ga:appInstallerId', u'ga:appName', u'ga:appVersion', u'ga:browser', u'ga:browserVersion', u'ga:campaign', u'ga:city', u'ga:continent', u'ga:country', u'ga:currencyCode', u'ga:customVarNameXX', u'ga:customVarValueXX', u'ga:date', u'ga:dateHour', u'ga:day', u'ga:dayOfWeek', u'ga:dayOfWeekName', u'ga:daysSinceLastVisit', u'ga:daysToTransaction', u'ga:deviceCategory', u'ga:dimensionXX', u'ga:eventAction', u'ga:eventCategory', u'ga:eventLabel', u'ga:exceptionDescription', u'ga:exitPagePath', u'ga:exitScreenName', u'ga:experimentId', u'ga:experimentVariant', u'ga:flashVersion', u'ga:fullReferrer', u'ga:goalCompletionLocation', u'ga:goalPreviousStep1', u'ga:goalPreviousStep2', u'ga:goalPreviousStep3', u'ga:hasSocialSourceReferral', u'ga:hostname', u'ga:hour', u'ga:interestAffinityCategory', u'ga:interestInMarketCategory', u'ga:interestOtherCategory', u'ga:isMobile', u'ga:isTablet', u'ga:isoWeek', u'ga:isoYear', u'ga:isoYearIsoWeek', u'ga:javaEnabled', u'ga:keyword', u'ga:landingPagePath', u'ga:landingScreenName', u'ga:language', u'ga:latitude', u'ga:longitude', u'ga:medium', u'ga:metro', u'ga:minute', u'ga:mobileDeviceBranding', u'ga:mobileDeviceInfo', u'ga:mobileDeviceMarketingName', u'ga:mobileDeviceModel', u'ga:mobileInputSelector', u'ga:month', u'ga:networkDomain', u'ga:networkLocation', u'ga:nextPagePath', u'ga:nthDay', u'ga:nthMinute', u'ga:nthMonth', u'ga:nthWeek', u'ga:operatingSystem', u'ga:operatingSystemVersion', u'ga:pageDepth', u'ga:pagePath', u'ga:pagePathLevel1', u'ga:pagePathLevel2', u'ga:pagePathLevel3', u'ga:pagePathLevel4', u'ga:pageTitle', u'ga:previousPagePath', u'ga:productCategory', u'ga:productName', u'ga:productSku', u'ga:referralPath', u'ga:region', u'ga:screenColors', u'ga:screenDepth', u'ga:screenName', u'ga:screenResolution', u'ga:searchCategory', u'ga:searchDestinationPage', u'ga:searchKeyword', u'ga:searchKeywordRefinement', u'ga:searchStartPage', u'ga:searchUsed', u'ga:secondPagePath', u'ga:socialActivityAction', u'ga:socialActivityContentUrl', u'ga:socialActivityDisplayName', u'ga:socialActivityEndorsingUrl', u'ga:socialActivityNetworkAction', u'ga:socialActivityPost', u'ga:socialActivityTagsSummary', u'ga:socialActivityTimestamp', u'ga:socialActivityUserHandle', u'ga:socialActivityUserPhotoUrl', u'ga:socialActivityUserProfileUrl', u'ga:socialEngagementType', u'ga:socialInteractionAction', u'ga:socialInteractionNetwork', u'ga:socialInteractionNetworkAction', u'ga:socialInteractionTarget', u'ga:socialNetwork', u'ga:source', u'ga:sourceMedium', u'ga:subContinent', u'ga:transactionId', u'ga:userDefinedValue', u'ga:userTimingCategory', u'ga:userTimingLabel', u'ga:userTimingVariable', u'ga:visitCount', u'ga:visitLength', u'ga:visitorAgeBracket', u'ga:visitorGender', u'ga:visitorType', u'ga:sessionsToTransaction', u'ga:week', u'ga:year', u'ga:yearMonth', u'ga:yearWeek',]

# Generated with:
#   import json
#   r = json.load(open('docs/ga-columns.json'))
#   dimensions = sorted(i['id'] for i in r['items'] if i['attributes'][u'type'] == u'DIMENSION')
#   metrics = sorted(i['id'] for i in r['items'] if i['attributes'][u'type'] == u'METRIC')
"""

from itertools import cycle

from briefmetrics.lib.service.google import Query
from briefmetrics.lib.table import Table

_response_profiles = {
    u"items": None,
    u"itemsPerPage": 1000,
    u"kind": u"analytics#profiles",
    u"startIndex": 1,
    u"totalResults": 0,
    u"username": u"example@example.com"
}

_response_data = {
    u"rows": None,
    u"totalResults": 0,
}

profile_item_template = {
    u"accountId": u"100001",
    u"created": u"2006-06-11T05:04:23.000Z",
    u"currency": u"USD",
    u"id": u"200000",
    u"internalWebPropertyId": u"300000",
    u"kind": u"analytics#profile",
    u"name": u"example.com",
    u"timezone": u"America/Toronto",
    u"type": u"WEB",
    u"updated": u"2011-09-29T20:00:34.864Z",
    u"webPropertyId": u"UA-111114-1",
    u"websiteUrl": u"example.com",
}

data = {}
data['ga:pageviews'] = data['ga:users'] = data['ga:sessions'] = [1000, 1001, 1884, 1999, 1399, 890, 1011]
data['ga:sessionDuration'] = [0.0, 0.123, 123.0, 0.5]
data['ga:avgSessionDuration'] = [0.0, 0.123, 123.0, 0.5]
data['ga:avgPageLoadTime'] = [0.0, 0.123, 123.0, 0.5]
data['ga:nthWeek'] = [1, 2]
data['ga:month'] = ['01'] * 6 + ['02'] * 4
data['ga:yearMonth'] = ['201501'] * 6 + ['201502'] * 4
data['ga:bounceRate'] = [0.1234, 0.2, 0.6999]
data['ga:date'] = ['2013-01-01', '2013-01-02']
data['ga:source'] = ['google', 'wordpress']
data['ga:socialNetwork'] = ['Facebook', 'Reddit']
data['ga:fullReferrer'] = ['example.com/foo', 'example.com/bar']
data['ga:pagePath'] = ['/foo', '/bar', '/baz']
data['ga:country'] = ['United States', 'Canada', 'Germany']
data['ga:deviceCategory'] = ['mobile', 'tablet', 'desktop']
data['ga:browser'] = ['Chrome', 'Firefox', 'Internet Explorer']
data['ga:goalConversionRateAll'] = [0.0, 0.123, 0.0]
data['ga:productName'] = ['Product A', 'Product B']
data['ga:itemRevenue'] = [0.0, 23.2, 42]
data['ga:itemQuantity'] = [0, 3, 11]
data['ga:adCost'] = [0.0, 23.2, 42]
data['ga:impressions'] = [0, 450, 9011]
data['ga:adClicks'] = [0, 30, 400]

skip_state = set(['ga:month'])


class FakeQuery(Query):
    def __init__(self, *args, **kw):
        super(FakeQuery, self).__init__(*args, **kw)
        self.num_profiles = kw.get('_num_profiles', 5)
        self.num_rows = kw.get('_num_rows', 10)

        self.cycles = {}

    def _stateful_cycle(self, col_id):
        r = cycle(data[col_id])
        if col_id in skip_state:
            return r
        return self.cycles.setdefault(col_id, r)

    def get(self, url, params=None):
        return {}

    def get_table(self, params, dimensions=None, metrics=None, _cache_keys=None):
        columns = self._columns_to_params(params, dimensions=dimensions, metrics=metrics)

        limit = min(self.num_rows, int(params.get('max-results', 10)))

        t = Table(columns)
        row_data = [self._stateful_cycle(col.id) for col in columns]
        for _ in xrange(limit):
            t.add(next(c) for c in row_data)

        return t

    def _get_profiles(self):
        r = _response_profiles.copy()
        r[u'items'] = []

        start_id = int(profile_item_template[u'id'])
        start_internalId = int(profile_item_template[u'internalWebPropertyId'])
        for i in xrange(self.num_profiles):
            t = profile_item_template.copy()
            t[u'id'] = unicode(start_id + i)
            t[u'internalWebPropertyId'] = unicode(start_internalId + i)
            r[u'items'].append(t)

        r[u'totalResults'] = len(r[u'items'])

        return r

    def get_profiles(self):
        r = self._get_profiles()
        return r[u'items']

    def get_profile(self, remote_id=None):
        return next(iter(self.get_profiles()))
