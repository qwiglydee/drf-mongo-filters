import re
from bson import ObjectId
from bson.errors import InvalidId
from django.utils.encoding import smart_str
from django.utils.datastructures import MultiValueDict
from rest_framework import fields
from rest_framework.exceptions import ValidationError

class DateTime000Field(fields.DateTimeField):
    """ discards microseconds """
    def to_internal_value(self, value):
        value = super().to_internal_value(value)
        return value.replace(microsecond=value.microsecond//1000*1000)

class ObjectIdField(fields.Field):
    type_label = 'ObjectIdField'

    def to_representation(self, value):
        return smart_str(value)

    def to_internal_value(self, data):
        try:
            return ObjectId(data)
        except InvalidId as e:
            raise ValidationError(e)

class ListField(fields.ListField):
    """ parses list of values under field_name
    like in ?foo=1&foo=2&foo=3 to [1,2,3]
    """
    def get_value(self, data):
        if isinstance(data, MultiValueDict):
            ret = data.getlist(self.field_name, fields.empty)
        elif isinstance(data, dict):
            ret = data.get(self.field_name, fields.empty)
        else:
            raise ValidationError("not a dict: " + str(type(data)))
        if ret == ['']:
            ret = fields.empty
        return ret

    def to_internal_value(self, data):
        if not hasattr(data, '__iter__'):
            raise ValidationError("not a list: " + str(type(data)))
        return [self.child.run_validation(item) for item in data]

class DictField(fields.DictField):
    """ parses dict of values under field_name-prefixed
    like in ?foo.bar=1&foo.baz=2 to { bar: 1, baz: 2 }
    """
    valid_keys = None
    required_keys = None

    def __init__(self, valid_keys=None, required_keys=None, **kwargs):
        if valid_keys:
            self.valid_keys = valid_keys
        if self.valid_keys is not None:
            self.valid_keys = set(self.valid_keys)

        if required_keys:
            self.required_keys = required_keys
        if self.required_keys is not None:
            self.required_keys = set(self.required_keys)

        super().__init__(**kwargs)

    def get_value(self, data):
        if isinstance(data, MultiValueDict):
            regex = re.compile(r"^%s\.(.*)$" % re.escape(self.field_name))
            ret = {}
            for name, value in data.items():
                match = regex.match(name)
                if not match:
                    continue
                key = match.groups()[0]
                if value != '':
                    ret[key] = value
        elif isinstance(data, dict):
            ret = data.get(self.field_name, fields.empty)
        else:
            raise ValidationError("not a dict: " + str(type(data)))

        if ret is fields.empty or len(ret) == 0:
            return fields.empty
        return ret

    def to_internal_value(self, data):
        if not hasattr(data, '__getitem__') or not hasattr(data, 'items'):
            raise ValidationError("not a dict: " + str(type(data)))

        keys = set(data.keys())
        if self.valid_keys is not None:
            if not keys <= self.valid_keys:
                raise ValidationError("invalid keys in dict: " + str(keys))

        if self.required_keys is not None:
            if not keys >= self.required_keys:
                raise ValidationError("missing required keys in dict: " + str(keys))

        return dict([
            (str(key), self.child.run_validation(value))
            for key, value in data.items()
        ])

class RangeField(DictField):
    valid_keys = ('min', 'max')

class GeoPointField(DictField):
    """ geo coordinates """
    valid_keys = ('lng', 'lat')
    required_keys = ('lng', 'lat')

    def __init__(self, **kwargs):
        kwargs['child'] = fields.FloatField()
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return { 'type': 'Point', 'coordinates': [ value['lng'], value['lat'] ] }
