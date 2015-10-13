from briefmetrics import test
from briefmetrics.lib import helpers as h


class TestHelpers(test.TestCase):

    def test_human_url(self):
        data = [
            ('https://google.com/', 'google.com'),
            ('google.com/', 'google.com'),
            ('google.com', 'google.com'),
            ('https://google.com/foo/', 'google.com/foo'),
            ('https://google.com/foo', 'google.com/foo'),
            ('//google.com/foo', 'google.com/foo'),
            ('://google.com/foo', 'google.com/foo'),
            ('google.com/foo/', 'google.com/foo'),
            ('google.com/foo', 'google.com/foo'),
            ('/foo', 'foo'),
        ]

        for input, expected in data:
            self.assertEqual(h.human_url(input), expected)

    def test_human_link(self):
        data = [
            ('https://google.com/', '<a href="https://google.com/">google.com</a>'),
            ('https://google.com/foo/', '<a href="https://google.com/foo/">google.com/foo</a>'),
            ('//google.com/', '<a href="http://google.com/">google.com</a>'),
            ('google.com', '<a href="http://google.com">google.com</a>'),
            ('google.com is great', 'google.com is great'),
            ('google.com/is+great', '<a href="http://google.com/is+great">google.com/is+great</a>'),
        ]

        for input, href in data:
            self.assertEqual(str(h.human_link(input)), href)

    def test_format_int(self):
        self.assertEqual(h.format_int(123, u'{:,} view'), u'123 views')
        self.assertEqual(h.format_int(1234, u'{:,} view'), u'1,234 views')
        self.assertEqual(h.format_int(1, u'{:,} view'), u'1 view')
