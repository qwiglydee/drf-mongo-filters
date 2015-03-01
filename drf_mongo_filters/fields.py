import re
from django.http import QueryDict
from rest_framework import fields
from rest_framework.exceptions import ValidationError

class ListField(fields.ListField):
    """ parses list of values under field_name
    like in ?foo=1&foo=2&foo=3 to [1,2,3]
    """
    def get_value(self, querydict):
        if not isinstance(querydict, QueryDict):
            raise ValidationError("not a querydict: " + str(type(querydict)))
        ret = querydict.getlist(self.field_name, fields.empty)
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
    def get_value(self, querydict):
        if not isinstance(querydict, QueryDict):
            raise ValidationError("not a querydict: " + str(type(querydict)))

        regex = re.compile(r"^%s\.(.*)$" % re.escape(self.field_name))
        ret = {}
        for name, value in querydict.items():
            match = regex.match(name)
            if not match:
                continue
            key = match.groups()[0]
            if value != '':
                ret[key] = value
        if len(ret) == 0:
            return fields.empty
        return ret

    def to_internal_value(self, data):
        if not hasattr(data, '__getitem__') or not hasattr(data, 'items'):
            raise ValidationError("not a list: " + str(type(data)))
        return dict([
            (str(key), self.child.run_validation(value))
            for key, value in data.items()
        ])
