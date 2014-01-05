from itertools import izip


class Column(object):
    def __init__(self, id, label=None, type_cast=None, type_format=None, visible=None, reverse=False, average=None, threshold=None):
        self.table = None
        self.id = id
        self.label = label or id
        self.type_cast = type_cast
        self.type_format = type_format
        self.visible = visible
        self.reverse = reverse

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

    def new(self):
        return Column(self.id, label=self.label, type_cast=self.type_cast, type_format=self.type_format, visible=self.visible, reverse=self.reverse, average=self.average)

    def cast(self, value):
        return self.type_cast(value) if self.type_cast else value

    def format(self, value):
        return self.type_format(value) if self.type_format else value

    def delta_value(self, value):
        return self._average is not None and (self._average - value) / (self._average or 1)

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
        if value is None:
            return True

        max_value, _ = self.max_row
        if not max_value:
            return False

        return not value or value < max_value * threshold

    def __repr__(self):
        return '{class_name}(id={self.id!r})'.format(class_name=self.__class__.__name__, self=self)


class RowTag(object):
    def __init__(self, column, value, type=None):
        self.column = column
        self.value = value
        self.type = type

    @property
    def delta_value(self):
        return self.column.delta_value(self.value)

    @property
    def is_positive(self):
        return (self.type == 'max') != self.column.reverse

    def __str__(self):
        parts = []

        if self.type in ['min', 'max']:
            pos = int(self.is_positive)
            adjective = ['Worst', 'Best'][pos]
            parts.append(adjective)

        parts.append(self.column.label)
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

    def add(self, row):
        values = []
        r = Row(self, values)
        for column, value in izip(self.columns, row):
            if not column:
                continue

            value = column.cast(value)
            if column.visible is not None and column.is_boring(value):
                # Skip row
                return

            values.append(value)
            if value is not None:
                column.measure(value, r)

        self.rows.append(r)

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
                row.tags.append(RowTag(column=column, value=value, type='max'))

            value, row = column.min_row
            if row and column.is_interesting(value):
                row.tags.append(RowTag(column=column, value=value, type='min'))

    def iter_rows(self, *column_ids):
        if not column_ids:
            column_ids = [col.id for col in self.columns]

        column_positions = [self.column_to_index[id] for id in column_ids]
        for row in self.rows:
            yield (row.values[i] for i in column_positions)

    def iter_visible(self):
        ordered_columns = self.get_visible()
        yield ordered_columns

        column_positions = [self.column_to_index[c.id] for c in ordered_columns]
        for row in self.rows:
            yield (row.values[i] for i in column_positions)

    def __json__(self):
        # TODO: ...
        return {'_response_data': self._response_data}
