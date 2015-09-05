from briefmetrics import test
from briefmetrics.lib.table import Column, Table
from briefmetrics.lib.report import split_table_delta


class TestTable(test.TestCase):
    def test_column(self):
        s = Column('foo', type_cast=int)
        self.assertEqual(s.cast('123'), 123)
        self.assertEqual(s.min_row, (None, None))
        self.assertEqual(s.max_row, (None, None))

        s = Column('foo', average=100, threshold=0.25)
        self.assertEqual(s.min_row, (100.0, None))
        self.assertEqual(s.max_row, (100.0, None))

        self.assertFalse(s.is_interesting(90))
        s.measure(90, 'a')
        self.assertEqual(s.min_row, (90.0, 'a'))
        self.assertEqual(s.max_row, (100.0, None))

        self.assertTrue(s.is_interesting(50))
        s.measure(50, 'b')
        self.assertEqual(s.min_row, (50.0, 'b'))
        self.assertEqual(s.max_row, (100.0, None))

        self.assertTrue(s.is_interesting(150))
        s.measure(150, 'c')
        self.assertEqual(s.min_row, (50.0, 'b'))
        self.assertEqual(s.max_row, (150.0, 'c'))

        self.assertTrue(s.is_interesting(200))
        s.measure(200, 'd')
        self.assertEqual(s.min_row, (50.0, 'b'))
        self.assertEqual(s.max_row, (200.0, 'd'))

    def test_rows(self):
        def positive_int(n):
            if not n or n < 0:
                return
            return int(n)

        t = Table([
            Column('foo', visible=1),
            Column('bar', visible=0),
            Column('baz', type_cast=positive_int, average=100),
        ])

        data = [
            (9999, '1', 123),
            (123, '2', 1234),
            (0000, '3', 23),
            (123, '4', 123),
            (123, '5', 0),
        ]

        for d in data:
            t.add(d)

        self.assertEqual(len(t.rows), len(data))
        self.assertEqual(t.get('foo').min_row, (None, None))
        self.assertEqual(t.get('bar').max_row, (None, None))
        self.assertEqual(t.get('baz').min_row[0], 23)
        self.assertEqual(t.get('baz').max_row[0], 1234)

        rows = t.iter_visible()
        self.assertEqual(list(next(rows)), [t.columns[1], t.columns[0]])
        self.assertEqual(list(next(rows)), ['1', 9999])

        t.tag_rows()
        self.assertFalse(t.rows[-1].tags)

class TestSplitTableDelta(test.TestCase):
    def test_join(self):
        t = Table([
            Column('value'),
            Column('joincol'),
            Column('splitcol'),
        ])
        expected = t.new()

        t.add((1, 'foo', 'a'))
        t.add((2, 'bar', 'a'))
        t.add((3, 'baz', 'a'))
        t.add((8, 'bar', 'b'))
        t.add((7, 'baz', 'b'))
        t.add((6, 'quux', 'b'))

        expected.add((1, 'foo', 'a'))
        expected.add((2, 'bar', 'a')).tag('Value', -6)
        expected.add((3, 'baz', 'a')).tag('Value', -4)

        split_table_delta(t, 'splitcol', 'joincol', 'value')
        self.assertEqual(dump(t), dump(expected))

def dump(table):
    return [repr(row) for row in table.rows]
