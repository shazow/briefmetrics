from briefmetrics.lib.cache import ReportRegion
from briefmetrics.lib.http import assert_response
from briefmetrics.lib.table import Table
from briefmetrics.lib.oauth import OAuth2API


class GoogleAPI(OAuth2API):
    config = {
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


def create_query(request, oauth):
    if request.features.get('offline'):
        from briefmetrics.test.fixtures.api_google import FakeQuery
        return FakeQuery(oauth)

    return Query(oauth)


# Generated with:
# > import json
# > r = json.load(open('docs/ga-columns.json'))
# > dimensions = sorted(i['id'] for i in r['items'] if i['attributes'][u'type'] == u'DIMENSION')
# > metrics = sorted(i['id'] for i in r['items'] if i['attributes'][u'type'] == u'METRIC')

#METRICS = [u'ga:CPC', u'ga:CPM', u'ga:CTR', u'ga:ROI', u'ga:RPC', u'ga:adClicks', u'ga:adCost', u'ga:adsenseAdUnitsViewed', u'ga:adsenseAdsClicks', u'ga:adsenseAdsViewed', u'ga:adsenseCTR', u'ga:adsenseECPM', u'ga:adsenseExits', u'ga:adsensePageImpressions', u'ga:adsenseRevenue', u'ga:appviews', u'ga:appviewsPerVisit', u'ga:avgDomContentLoadedTime', u'ga:avgDomInteractiveTime', u'ga:avgDomainLookupTime', u'ga:avgEventValue', u'ga:avgPageDownloadTime', u'ga:avgPageLoadTime', u'ga:avgRedirectionTime', u'ga:avgScreenviewDuration', u'ga:avgSearchDepth', u'ga:avgSearchDuration', u'ga:avgSearchResultViews', u'ga:avgServerConnectionTime', u'ga:avgServerResponseTime', u'ga:avgTimeOnPage', u'ga:avgTimeOnSite', u'ga:avgUserTimingValue', u'ga:bounces', u'ga:costPerConversion', u'ga:costPerGoalConversion', u'ga:costPerTransaction', u'ga:domContentLoadedTime', u'ga:domInteractiveTime', u'ga:domLatencyMetricsSample', u'ga:domainLookupTime', u'ga:entranceBounceRate', u'ga:entranceRate', u'ga:entrances', u'ga:eventValue', u'ga:eventsPerVisitWithEvent', u'ga:exceptions', u'ga:exceptionsPerScreenview', u'ga:exitRate', u'ga:exits', u'ga:fatalExceptions', u'ga:fatalExceptionsPerScreenview', u'ga:goalAbandonRateAll', u'ga:goalAbandonsAll', u'ga:goalCompletionsAll', u'ga:goalConversionRateAll', u'ga:goalStartsAll', u'ga:goalValueAll', u'ga:goalValueAllPerSearch', u'ga:goalValuePerVisit', u'ga:goalXXAbandonRate', u'ga:goalXXAbandons', u'ga:goalXXCompletions', u'ga:goalXXConversionRate', u'ga:goalXXStarts', u'ga:goalXXValue', u'ga:impressions', u'ga:itemQuantity', u'ga:itemRevenue', u'ga:itemsPerPurchase', u'ga:localItemRevenue', u'ga:localTransactionRevenue', u'ga:localTransactionShipping', u'ga:localTransactionTax', u'ga:margin', u'ga:metricXX', u'ga:newVisits', u'ga:organicSearches', u'ga:pageDownloadTime', u'ga:pageLoadSample', u'ga:pageLoadTime', u'ga:pageValue', u'ga:pageviews', u'ga:pageviewsPerVisit', u'ga:percentNewVisits', u'ga:percentSearchRefinements', u'ga:percentVisitsWithSearch', u'ga:redirectionTime', u'ga:revenuePerItem', u'ga:revenuePerTransaction', u'ga:screenviews', u'ga:screenviewsPerSession', u'ga:searchDepth', u'ga:searchDuration', u'ga:searchExitRate', u'ga:searchExits', u'ga:searchGoalConversionRateAll', u'ga:searchGoalXXConversionRate', u'ga:searchRefinements', u'ga:searchResultViews', u'ga:searchUniques', u'ga:searchVisits', u'ga:serverConnectionTime', u'ga:serverResponseTime', u'ga:socialActivities', u'ga:socialInteractions', u'ga:socialInteractionsPerVisit', u'ga:speedMetricsSample', u'ga:timeOnPage', u'ga:timeOnScreen', u'ga:timeOnSite', u'ga:totalEvents', u'ga:totalValue', u'ga:transactionRevenue', u'ga:transactionRevenuePerVisit', u'ga:transactionShipping', u'ga:transactionTax', u'ga:transactions', u'ga:transactionsPerVisit', u'ga:uniqueAppviews', u'ga:uniqueEvents', u'ga:uniquePageviews', u'ga:uniquePurchases', u'ga:uniqueScreenviews', u'ga:uniqueSocialInteractions', u'ga:userTimingSample', u'ga:userTimingValue', u'ga:visitBounceRate', u'ga:visitors', u'ga:visits', u'ga:visitsWithEvent']
#DIMENSIONS = [u'ga:adContent', u'ga:adDestinationUrl', u'ga:adDisplayUrl', u'ga:adDistributionNetwork', u'ga:adFormat', u'ga:adGroup', u'ga:adKeywordMatchType', u'ga:adMatchType', u'ga:adMatchedQuery', u'ga:adPlacementDomain', u'ga:adPlacementUrl', u'ga:adSlot', u'ga:adSlotPosition', u'ga:adTargetingOption', u'ga:adTargetingType', u'ga:adwordsAdGroupID', u'ga:adwordsCampaignID', u'ga:adwordsCreativeID', u'ga:adwordsCriteriaID', u'ga:adwordsCustomerID', u'ga:affiliation', u'ga:appId', u'ga:appInstallerId', u'ga:appName', u'ga:appVersion', u'ga:browser', u'ga:browserVersion', u'ga:campaign', u'ga:city', u'ga:continent', u'ga:country', u'ga:currencyCode', u'ga:customVarNameXX', u'ga:customVarValueXX', u'ga:date', u'ga:dateHour', u'ga:day', u'ga:dayOfWeek', u'ga:dayOfWeekName', u'ga:daysSinceLastVisit', u'ga:daysToTransaction', u'ga:deviceCategory', u'ga:dimensionXX', u'ga:eventAction', u'ga:eventCategory', u'ga:eventLabel', u'ga:exceptionDescription', u'ga:exitPagePath', u'ga:exitScreenName', u'ga:experimentId', u'ga:experimentVariant', u'ga:flashVersion', u'ga:fullReferrer', u'ga:goalCompletionLocation', u'ga:goalPreviousStep1', u'ga:goalPreviousStep2', u'ga:goalPreviousStep3', u'ga:hasSocialSourceReferral', u'ga:hostname', u'ga:hour', u'ga:interestAffinityCategory', u'ga:interestInMarketCategory', u'ga:interestOtherCategory', u'ga:isMobile', u'ga:isTablet', u'ga:isoWeek', u'ga:isoYear', u'ga:isoYearIsoWeek', u'ga:javaEnabled', u'ga:keyword', u'ga:landingPagePath', u'ga:landingScreenName', u'ga:language', u'ga:latitude', u'ga:longitude', u'ga:medium', u'ga:metro', u'ga:minute', u'ga:mobileDeviceBranding', u'ga:mobileDeviceInfo', u'ga:mobileDeviceMarketingName', u'ga:mobileDeviceModel', u'ga:mobileInputSelector', u'ga:month', u'ga:networkDomain', u'ga:networkLocation', u'ga:nextPagePath', u'ga:nthDay', u'ga:nthMinute', u'ga:nthMonth', u'ga:nthWeek', u'ga:operatingSystem', u'ga:operatingSystemVersion', u'ga:pageDepth', u'ga:pagePath', u'ga:pagePathLevel1', u'ga:pagePathLevel2', u'ga:pagePathLevel3', u'ga:pagePathLevel4', u'ga:pageTitle', u'ga:previousPagePath', u'ga:productCategory', u'ga:productName', u'ga:productSku', u'ga:referralPath', u'ga:region', u'ga:screenColors', u'ga:screenDepth', u'ga:screenName', u'ga:screenResolution', u'ga:searchCategory', u'ga:searchDestinationPage', u'ga:searchKeyword', u'ga:searchKeywordRefinement', u'ga:searchStartPage', u'ga:searchUsed', u'ga:secondPagePath', u'ga:socialActivityAction', u'ga:socialActivityContentUrl', u'ga:socialActivityDisplayName', u'ga:socialActivityEndorsingUrl', u'ga:socialActivityNetworkAction', u'ga:socialActivityPost', u'ga:socialActivityTagsSummary', u'ga:socialActivityTimestamp', u'ga:socialActivityUserHandle', u'ga:socialActivityUserPhotoUrl', u'ga:socialActivityUserProfileUrl', u'ga:socialEngagementType', u'ga:socialInteractionAction', u'ga:socialInteractionNetwork', u'ga:socialInteractionNetworkAction', u'ga:socialInteractionTarget', u'ga:socialNetwork', u'ga:source', u'ga:sourceMedium', u'ga:subContinent', u'ga:transactionId', u'ga:userDefinedValue', u'ga:userTimingCategory', u'ga:userTimingLabel', u'ga:userTimingVariable', u'ga:visitCount', u'ga:visitLength', u'ga:visitorAgeBracket', u'ga:visitorGender', u'ga:visitorType', u'ga:visitsToTransaction', u'ga:week', u'ga:year', u'ga:yearMonth', u'ga:yearWeek',]


class Query(object):
    def __init__(self, oauth):
        self.api = oauth

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

    def get_table(self, params, dimensions=None, metrics=None, _cache_keys=None):
        params = dict(params)
        columns = self._columns_to_params(params, dimensions=dimensions, metrics=metrics)

        t = Table(columns)
        t._response_data = response_data = self._get_data(params, _cache_keys=_cache_keys)
        if 'rows' not in response_data:
            return t

        for row in response_data['rows']:
            t.add(row)

        return t

    def get_profiles(self, account_id):
        # account_id used for caching, not in query.
        return self._get('https://www.googleapis.com/analytics/v3/management/accounts/~all/webproperties/~all/profiles', _cache_keys=(account_id,))
