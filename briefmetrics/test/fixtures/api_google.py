_response_profiles = {
    "items": None,
    "itemsPerPage": 1000,
    "kind": "analytics#profiles",
    "startIndex": 1,
    "totalResults": 0,
    "username": "example@example.com"
}

_response_data = {
    "rows": None,
    "totalResults": 0,
}

_profile_item_template = {
    "accountId": "111111",
    "created": "2006-06-11T05:04:23.000Z",
    "currency": "USD",
    "id": "111112",
    "internalWebPropertyId": "111113",
    "kind": "analytics#profile",
    "name": "example.com",
    "timezone": "America/Toronto",
    "type": "WEB",
    "updated": "2011-09-29T20:00:34.864Z",
    "webPropertyId": "UA-111114-1",
    "websiteUrl": "example.com",
}


class FakeQuery(object):
    num_profiles = 5

    def __init__(self, *args, **kw):
        pass

    def get_profiles(self, account_id):
        r = _response_profiles.copy()
        r['items'] = []

        for i in xrange(self.num_profiles):
            t = _profile_item_template.copy()
            r['items'].append(t)

        r['totalResults'] = len(r['items'])

        return r

    def report_summary(self, id, date_start, date_end):
        r = _response_data.copy()
        r['rows'] = []

        for i in xrange(2):
            r['rows'].append([
                "42",
                "3778",
                "3964",
                "349384.0",
                "22.5"
            ])

        return r

    def report_referrers(self, id, date_start, date_end):
        r = _response_data.copy()
        r['rows'] = []

        for i in xrange(10):
            r['rows'].append([
                "example.com/somelist",
                "20",
            ])

        return r

    def report_pages(self, id, date_start, date_end):
        r = _response_data.copy()
        r['rows'] = []

        for i in xrange(10):
            r['rows'].append([
                "1000",
                "500",
                "345",
            ])

        return r

    def report_social(self, id, date_start, date_end):
        r = _response_data.copy()
        r['rows'] = []

        for i in xrange(10):
            r['rows'].append([
                "Pinterest",
                "243",
            ])

        return r

    def report_historic(self, id, date_start, date_end):
        r = _response_data.copy()
        r['rows'] = []

        for i in xrange(29):
            r['rows'].append([
                "201309%d" % (i + 1),
                "09",
                "146",
            ])

        for i in xrange(7):
            r['rows'].append([
                "201310%d" % (i + 1),
                "10",
                "147",
            ])

        return r
