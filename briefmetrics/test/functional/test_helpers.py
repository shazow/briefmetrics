from briefmetrics import test
from briefmetrics.lib import helpers as h


class TestHelpers(test.TestWeb):

    def test_human_url(self):
        data = [
            ('https://google.com/', 'google.com'),
            ('google.com/', 'google.com'),
            ('google.com', 'google.com'),
            ('https://google.com/foo/', 'google.com/foo'),
            ('https://google.com/foo', 'google.com/foo'),
            ('google.com/foo/', 'google.com/foo'),
            ('google.com/foo', 'google.com/foo'),
        ]

        for input, expected in data:
            self.assertEqual(h.human_url(input), expected)

    def test_human_link(self):
        data = [
            ('https://google.com/', '<a href="https://google.com/">google.com</a>'),
            ('https://google.com/foo/', '<a href="https://google.com/foo/">google.com/foo</a>'),
        ]

        for input, href in data:
            self.assertEqual(str(h.human_link(input)), href)
