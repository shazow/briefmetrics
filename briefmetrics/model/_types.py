from sqlalchemy import types
from sqlalchemy.ext.mutable import Mutable

import collections
import datetime
import json
import time


class SchemaEncoder(json.JSONEncoder):
    """Encoder for converting Model objects into JSON."""

    def default(self, obj):
        if isinstance(obj, datetime.date):
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', obj.utctimetuple())
        elif hasattr(obj, '__json__'):
            return obj.__json__()
        return json.JSONEncoder.default(self, obj)


class Enum(types.TypeDecorator):
    impl = types.Integer

    def __init__(self, value_map, strict=True, *args, **kw):
        """Emulate Enum type with integer-based indexing.

        value_map:
            An integer_id:name dictionary of possible values, or a list of value
            names (which gets converted to corresponding index numbers starting from 1).
        strict:
            Assert that data read from the database matches with the expected
            valid value definitions.
        """

        self.strict = strict

        if isinstance(value_map, list):
            value_map = dict((k+1,v) for k,v in enumerate(value_map))

        # Enum lookup indices
        self.id_lookup = value_map
        self.name_lookup = dict((v,k) for k,v in value_map.iteritems())

        super(Enum, self).__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return

        id = self.name_lookup.get(value)
        if not id:
            raise AssertionError("Name '{0}' is not one of: {1}".format(value, self.name_lookup.keys()))
        return id

    def process_result_value(self, value, dialect):
        if value is None:
            return

        name = self.id_lookup.get(value)
        if self.strict and not name:
            raise AssertionError("Id '{0}' is not one of: {1}".format(value, self.id_lookup.keys()))
        return name

    def copy_value(self, value):
        "Convert named value to internal id representation"
        return self.name_lookup.get(value)


class JSONEncodedDict(types.TypeDecorator):
    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
        return value is not None and json.dumps(value, cls=SchemaEncoder)

    def process_result_value(self, value, dialect):
        return value is not None and json.loads(value) or {}


class MutationDict(dict, Mutable, collections.MutableMapping):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutationDict."
        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."
        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."
        dict.__delitem__(self, key)
        self.changed()

    def update(self, E, **F):
        dict.update(self, E, **F)
        self.changed()
