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


class FakeQuery(object):
    def __init__(self, *args, **kw):
        self.num_profiles = kw.get('_num_profiles', 5)
        self.num_rows = kw.get('_num_rows', 10)

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
