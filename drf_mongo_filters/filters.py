from mongoengine.queryset.transform import MATCH_OPERATORS
from rest_framework import fields
from rest_framework_mongoengine import fields as mongofields

from . import fields as comp_fields

class Filter():
    """ filter base class
    Wraps serializer field to parse value from querydict.
    Name of filter (as filterset attribute) or provided name refers to key in querydict.
    Source of field (or filter name) refers to model attribute the filter will be applied.

    Attrs:
    - field_class: class of serializer field
    - lookup_type: operator to use in queryset filtering, '=' to use simple comparision
    """
    field_class = fields.Field
    lookup_type = '='

    # to make skipped fields happy
    partial = True

    _creation_counter = 0
    def __init__(self, name=None, lookup_type=None, **kwargs):
        """
        Args:
        - name: override query_data argument name, defaults to binding name
        - lookup_type: override lookup operator
        - kwargs: args to pass to field constructor
        """
        self.name = name
        if lookup_type:
            self.lookup_type = lookup_type

        if self.lookup_type != '=' and self.lookup_type not in MATCH_OPERATORS:
            raise TypeError("invalid lookup type: " + repr(self.lookup_type))

        self.parent = None
        self.field = self.make_field(**kwargs)

        self._creation_order = Filter._creation_counter
        Filter._creation_counter += 1

    def make_field(self, **kwargs):
        """ create serializer field """
        kwargs['required'] = False
        kwargs['allow_null'] = True
        return self.field_class(**kwargs)

    def bind(self, name, filterset):
        """ attach filter to filterset

        gives a name to use to extract arguments from querydict
        """
        if self.name is not None:
            name = self.name
        self.field.bind(name, self)

    def parse_value(self, querydict):
        """ extract value

        extarct value from querydict and convert it to native
        missing and empty values result to None
        """
        value = self.field.get_value(querydict)
        if value in (None, fields.empty, ''):
            return None
        return self.field.to_internal_value(value)

    def filter_params(self, value):
        """ return filtering params """
        if value is None:
            return {}

        target = "__".join(self.field.source_attrs)
        if self.lookup_type != '=':
            target += '__' + self.lookup_type
        return { target: value }

class BooleanFilter(Filter):
    field_class = fields.NullBooleanField
    def make_field(self, **kwargs):
        kwargs['required'] = False
        return self.field_class(**kwargs)

class ExistsFilter(BooleanFilter):
    lookup_type = 'exists'

class CharFilter(Filter):
    field_class = fields.CharField

class UUIDFilter(Filter):
    field_class = fields.UUIDField

class IntegerFilter(Filter):
    field_class = fields.IntegerField

class FloatFilter(Filter):
    field_class = fields.FloatField

class DateTimeFilter(Filter):
    field_class = fields.DateTimeField

class DateFilter(Filter):
    field_class = fields.DateField

class TimeFilter(Filter):
    field_class = fields.TimeField

class ChoiceFilter(Filter):
    field_class = fields.ChoiceField

class ObjectIdFilter(Filter):
    field_class = mongofields.ObjectIdField
