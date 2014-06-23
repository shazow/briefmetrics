from itertools import izip
from unstdlib import html


TABLE, THEAD, TBODY, TR, TD = html.tag_builder(['table', 'thead', 'tbody', 'tr', 'td'])


class Column(object):
    def __init__(self, id, label=None, type_cast=None, type_format=None, type_class=None, visible=None, reverse=False, average=None, threshold=None, nullable=False):
        self.table = None
        self.id = id
        self.label = label if label is not None else id
        self.type_cast = type_cast
        self.type_format = type_format
        self.type_class = type_class
        self.visible = visible
        self.reverse = reverse
        self.nullable = nullable

        self._threshold = threshold
        self._average = average and float(average)

        if threshold is None and average is not None:
            self._threshold = 0.15

        self.min_row = average, None
        self.max_row = average, None
        self.sum = 0

    @property
    def average(self):
        if self._threshold is None:
            return
        return self.sum / float(len(self.table.rows) or 1)

    @property
    def median(self):
        num_rows = len(self.table.rows)
        if not num_rows:
            return 0

        return self.table.rows[num_rows/2].get(self.id)

    def new(self):
        return Column(self.id, label=self.label, type_cast=self.type_cast, type_format=self.type_format, visible=self.visible, reverse=self.reverse, average=self.average)

    def cast(self, value):
        return self.type_cast(value) if self.type_cast else value

    def format(self, value):
        return self.type_format(value) if self.type_format else str(value)

    def compute_average(self):
        self._average = self.average

    def delta_value(self, value):
        return self._average is not None and (self._average - value) / (self._average or 1.0)

    def measure(self, value, row):
        if value is None or self._threshold is None:
            return False

        self.sum += value

        min_value, _ = self.min_row
        if min_value > value:
            self.min_row = value, row

        max_value, _ = self.max_row
        if max_value < value:
            self.max_row = value, row

    def is_interesting(self, value):
        if value is None or self._threshold is None:
            return False

        delta = self.delta_value(value)
        if delta and abs(delta) < self._threshold:
            return False

        return True

    def is_boring(self, value, threshold=0.005):
        if value is None and not self.nullable:
            return True

        max_value, _ = self.max_row
        if not max_value:
            return False

        return not value or value < max_value * threshold

    def __repr__(self):
        return '{class_name}(id={self.id!r})'.format(class_name=self.__class__.__name__, self=self)


class RowTag(object):
    def __init__(self, type=None, value=None, column=None, is_positive=None, is_prefixed=False):
        self.type = type
        self.value = value
        self.column = column
        self.is_positive_override = is_positive
        self.is_prefixed = is_prefixed

    @property
    def delta_value(self):
        if not self.column or self.value is None:
            return

        return self.column.delta_value(self.value)

    @property
    def is_positive(self):
        if self.is_positive_override is not None:
            return self.is_positive_override

        if not self.column:
            return

        if self.type == 'min':
            return self.column.reverse
        elif self.type == 'max':
            return not self.column.reverse

        if self.value:
            return self.value > 0 ^ self.column.reverse

    def __str__(self):
        parts = []

        if self.column:
            parts.append(self.column.format(self.value))
            parts.append(self.column.label)
        else:
            if self.is_prefixed:
                parts.append(str(self.value))

            parts.append(self.type.title())

        return ' '.join(parts)


class Row(object):
    __slots__ = [
        'values',
        'table',
        'tags',
    ]

    def __init__(self, table, values):
        self.table = table
        self.values = values
        self.tags = []

    def get(self, id):
        return self.values[self.table.column_to_index[id]]

    def tag(self, type, value=None, column=None, **kw):
        self.tags.append(RowTag(type, column=column, value=value, **kw))

    def __repr__(self):
        return '{class_name}(values={self.values!r})'.format(class_name=self.__class__.__name__, self=self)


class Table(object):
    _response_data = None

    def __init__(self, columns):
        # Columns must be in the same order as the rows that get added.
        self.columns = columns
        self.rows = []
        self.column_to_index = {s.id: i for i, s in enumerate(columns)}

        for column in columns:
            column.table = self

    def add(self, row, is_measured=True):
        values = []
        r = Row(self, values)
        for column, value in izip(self.columns, row):
            if not column:
                continue

            value = column.cast(value)
            if is_measured and column.visible is not None and column.is_boring(value):
                # Skip row
                return

            values.append(value)
            if value is not None and is_measured:
                column.measure(value, r)

        self.rows.append(r)
        return r

    def sort(self, reverse=False):
        visible_columns = self.get_visible()
        column_pos = sorted((col.visible, self.column_to_index[col.id]) for col in visible_columns)
        self.rows.sort(key=lambda r: tuple(r.values[pos] for _, pos in column_pos), reverse=reverse)

    def get(self, id):
        "Return the column"
        return self.columns[self.column_to_index[id]]

    def get_visible(self):
        visible_columns = (c for c in self.columns if c.visible is not None)
        return sorted(visible_columns, key=lambda o: o.visible)

    def set_visible(self, *column_ids):
        pos_lookup = {id: i for i, id in enumerate(column_ids)}

        for column in self.columns:
            column.visible = pos_lookup.pop(column.id, None)

        if pos_lookup:
            raise KeyError('Invalid column ids: %r' % pos_lookup.keys())

    def tag_rows(self):
        if len(self.rows) < 3:
            return

        for column in self.columns:
            if column.visible is not None or column._threshold is None:
                # We only want non-visible thresholded columns
                continue

            value, row = column.max_row
            if row and column.is_interesting(value):
                row.tag(type='max', value=value, column=column)

            value, row = column.min_row
            if row and column.is_interesting(value):
                row.tag(type='min', value=value, column=column)

    def iter_rows(self, *column_ids):
        if not column_ids:
            column_ids = [col.id for col in self.columns]

        column_positions = [self.column_to_index[id] for id in column_ids]
        for row in self.rows:
            yield (row.values[i] for i in column_positions)

    def iter_visible(self, reverse=False):
        ordered_columns = self.get_visible()
        yield ordered_columns

        column_positions = [self.column_to_index[c.id] for c in ordered_columns]
        rows = self.rows if not reverse else reversed(self.rows)
        for row in rows:
            yield (row.values[i] for i in column_positions)

    def limit(self, num):
        "Truncate rows to `num`."
        self.rows = self.rows[:num]

    def render_html(self):
        rows = self.iter_visible()
        columns = next(rows)

        return TABLE(
            THEAD(
                TR(TD(col.label, attrs={'class': col.type_class}) for col in columns)
            ) +
            TBODY (
                TR(
                    TD(col.format(v), attrs={'class': col.type_class}) for col, v in izip(columns, row)
                ) for row in rows
            )
        )


    def __json__(self):
        # TODO: ...
        return {'_response_data': self._response_data}
