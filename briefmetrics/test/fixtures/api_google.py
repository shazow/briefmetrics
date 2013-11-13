from itertools import cycle

from briefmetrics.api.google import Query
from briefmetrics.lib.report import Table

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

_profile_item_template = {
    u"accountId": u"111111",
    u"created": u"2006-06-11T05:04:23.000Z",
    u"currency": u"USD",
    u"id": u"111112",
    u"internalWebPropertyId": u"111113",
    u"kind": u"analytics#profile",
    u"name": u"example.com",
    u"timezone": u"America/Toronto",
    u"type": u"WEB",
    u"updated": u"2011-09-29T20:00:34.864Z",
    u"webPropertyId": u"UA-111114-1",
    u"websiteUrl": u"example.com",
}

data = {}
data['ga:pageviews'] = data['ga:uniquePageviews'] = data['ga:visits'] = cycle([0, 123, 123456, 1234567, 123456, 123])
data['ga:timeOnSite'] = cycle([0.123, 123.0, 0.5])
data['ga:week'] = cycle([1, 2])
data['ga:month'] = cycle([1, 2])
data['ga:visitBounceRate'] = cycle([0.2, 0.6])
data['ga:date'] = cycle(['2013-01-01', '2013-01-02'])
data['ga:socialNetwork'] = cycle(['Facebook', 'Reddit'])
data['ga:fullReferrer'] = cycle(['example.com/foo', 'example.com/bar'])
data['ga:pagePath'] = cycle(['/foo', '/bar', '/baz'])


class FakeQuery(Query):
    def __init__(self, *args, **kw):
        self.num_profiles = kw.get('_num_profiles', 5)
        self.num_rows = kw.get('_num_rows', 10)

    def get_table(self, params, dimensions=None, metrics=None):
        columns = self._columns_to_params(params, dimensions=dimensions, metrics=metrics)

        limit = int(params.get('max-results', 10))

        t = Table(columns)
        for _ in xrange(limit):
            row = [next(data[col.id]) for col in columns]
            t.add(row)

        return t

    def get_profiles(self, account_id):
        r = _response_profiles.copy()
        r[u'items'] = []

        for i in xrange(self.num_profiles):
            t = _profile_item_template.copy()
            r[u'items'].append(t)

        r[u'totalResults'] = len(r[u'items'])

        return r

    def report_summary(self, id, date_start, date_end):
        r = _response_data.copy()
        r[u'rows'] = []

        for i in xrange(2):
            r[u'rows'].append([
                u"42",
                u"3778",
                u"3964",
                u"349384.0",
                u"22.5"
            ])

        return r

    def report_referrers(self, id, date_start, date_end):
        r = _response_data.copy()
        r[u'rows'] = []

        for i in xrange(self.num_rows):
            r[u'rows'].append([
                u"example.com/somelist",
                u"20",
            ])

        return r

    def report_pages(self, id, date_start, date_end):
        r = _response_data.copy()
        r[u'rows'] = []

        for i in xrange(self.num_rows):
            r[u'rows'].append([
                u"1000",
                u"500",
                u"345",
            ])

        return r

    def report_social(self, id, date_start, date_end):
        r = _response_data.copy()
        r[u'rows'] = []

        for i in xrange(self.num_rows):
            r[u'rows'].append([
                u"Pinterest",
                u"243",
            ])

        return r

    def report_historic(self, id, date_start, date_end):
        r = _response_data.copy()
        r[u'rows'] = []

        for i in xrange(29):
            r[u'rows'].append([
                u"201309%d" % (i + 1),
                u"09",
                u"146",
            ])

        for i in xrange(7):
            r[u'rows'].append([
                u"201310%d" % (i + 1),
                u"10",
                u"147",
            ])

        return r
