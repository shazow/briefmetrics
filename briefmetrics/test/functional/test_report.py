from briefmetrics import test
from briefmetrics import api
from briefmetrics import model
from briefmetrics.lib.exceptions import APIError

import mock
import json
import os
import datetime

Session = model.Session

response_fixtures_dir = os.path.join(os.path.dirname(__file__), '../fixtures/api_google_responses')


class TestReport(test.TestWeb):
    @classmethod
    def setUpClass(cls):
        super(TestReport, cls).setUpClass()
        mock_kw = {}

        for attr in api.google.Query.__dict__:
            if attr.startswith('_'):
                pass

            response_path = os.path.join(response_fixtures_dir, attr + '.json')
            if not os.path.exists(response_path):
                continue

            with open(response_path, 'r') as fp:
                try:
                    mock_kw[attr + '.return_value'] = json.load(fp)
                except ValueError as e:
                    raise ValueError('Failed to parse response fixture: %s (%s)' % (response_path, e))

        cls.MockQuery = mock.Mock(spec=api.google.Query, **mock_kw)
        api.google.Query = mock.Mock(return_value=cls.MockQuery)

    def test_fake_query(self):
        q = self.MockQuery
        r = q.get_profiles()
        self.assertEqual(r[u'username'], u'example@example.com')

        q = api.google.Query(None)
        r = q.get_profiles()
        self.assertEqual(r[u'username'], u'example@example.com')

    def test_fetch_weekly(self):
        remote_data = self.MockQuery.get_profiles()['items'][0]

        u = api.account.get_or_create(email=u'example@example.com', token={}, display_name=u'Example')
        report = model.Report.create(account=u.account, remote_data=remote_data, display_name=u'example.com')
        model.Subscription.create(user=u, report=report)
        Session.commit()

        context = api.report.fetch_weekly(self.request, report, datetime.date(2013, 1, 1))
        self.assertEqual(context.date_next, datetime.date(2013, 1, 8))
        self.assertEqual(context.subject, u'Weekly report \u2019til Jan 07: example.com')
