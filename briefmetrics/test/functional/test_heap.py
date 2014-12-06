import json
import mock

from briefmetrics import test
from briefmetrics.lib.service import heap


class TestHeapExtract(test.TestCase):
    def test_heap_extract(self):
        t = {
            'cu': u'USD',
            'hit_type': 'transaction',
            'user_id': None,
            'client_id': None,
            'items': [{'cu': u'USD',
                'hit_type': 'item',
                'user_id': None,
                'client_id': None,
                'in': u'Briefmetrics: Personal',
                'ip': 8.00,
                'iq': 1,
                'ti': u'in_4hiFBbDjuLsJ6T'}],
            'ti': u'in_4hiFBbDjuLsJ6T',
            'tr': 8.00}

        properties = heap.extract(t)
        self.assertEqual(properties, {
            'provider': 'stripe',
            'id': 'in_4hiFBbDjuLsJ6T',
            'total': 8.00,
            'currency': 'USD',
            'items': [{
                'amount': 8.00,
                'currency': 'USD',
                'quantity': 1,
                'description': 'Briefmetrics: Personal',
            }],
        })
