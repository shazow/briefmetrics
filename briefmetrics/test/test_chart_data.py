from briefmetrics import test

from briefmetrics.web.views.report import _encode_chart


class TestChartData(test.TestCase):
    def test_encode_chart(self):
        input = [
            ('20130101', '01', '100'),
            ('20130102', '01', '100'),
            ('20130103', '01', '100'),
            ('20130104', '01', '100'),
            ('20130105', '01', '100'),
            ('20130201', '02', '100'),
        ]

        expected_output = 't:20,40,60,80,100|20,_,_,_,_'
        self.assertEqual(_encode_chart(input), expected_output)

