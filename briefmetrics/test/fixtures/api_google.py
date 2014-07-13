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
data['ga:pageviews'] = data['ga:visitors'] = data['ga:visits'] = [1000, 1001, 1884, 1999, 1399, 890, 1011]
data['ga:timeOnSite'] = [0.0, 0.123, 123.0, 0.5]
data['ga:avgTimeOnSite'] = [0.0, 0.123, 123.0, 0.5]
data['ga:avgPageLoadTime'] = [0.0, 0.123, 123.0, 0.5]
data['ga:nthWeek'] = [1, 2]
data['ga:month'] = [1] * 6 + [2] * 4
data['ga:visitBounceRate'] = [0.1234, 0.2, 0.6999]
data['ga:date'] = ['2013-01-01', '2013-01-02']
data['ga:source'] = ['google', 'wordpress']
data['ga:socialNetwork'] = ['Facebook', 'Reddit']
data['ga:fullReferrer'] = ['example.com/foo', 'example.com/bar']
data['ga:pagePath'] = ['/foo', '/bar', '/baz']
data['ga:country'] = ['United States', 'Canada', 'Germany']
data['ga:deviceCategory'] = ['mobile', 'tablet', 'desktop']
data['ga:browser'] = ['Chrome', 'Firefox', 'Internet Explorer']
data['ga:goalConversionRateAll'] = [0.0, 0.123, 0.0]


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
