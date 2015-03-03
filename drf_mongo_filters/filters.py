from mongoengine.queryset import transform
from rest_framework import fields
from rest_framework_mongoengine.fields import ObjectIdField

from .fields import ListField, DictField

COMPARISION_OPERATORS = ('ne', 'gt', 'gte', 'lt', 'lte')

class Filter():
    """ filter base class
    Wraps serializer field to parse value from querydict.
    Name of filter (as filterset attribute) or provided name refers to key in querydict.
    Source of field (or filter name) refers to model attribute the filter will be applied.

    Attrs:
    - field_class: class of serializer field
    - lookup_type: operator to use in queryset filtering, None to use simple comparision
    """
    field_class = fields.Field
    lookup_type = None
    VALID_LOOKUPS = (None,) + COMPARISION_OPERATORS

    # to make skipped fields happy
    partial = True

    _creation_counter = 0
    def __init__(self, name=None, lookup=None, **kwargs):
        """
        Args:
        - name: override query_data argument name, defaults to binding name
        - lookup_type: override lookup operator
        - kwargs: args to pass to field constructor
        """
        self.name = name
        if lookup:
            self.lookup_type = lookup

        if self.lookup_type not in self.VALID_LOOKUPS:
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
        if self.lookup_type is not None:
            target += '__' + self.lookup_type
        return { target: value }

    def __str__(self):
        return "<%s %s__%s>" % (self.__class__.__name__, self.field.source, self.lookup_type or '')

class BooleanFilter(Filter):
    VALID_LOOKUPS = (None, 'ne', 'exists')
    field_class = fields.NullBooleanField
    def make_field(self, **kwargs):
        kwargs['required'] = False
        return self.field_class(**kwargs)

class ExistsFilter(BooleanFilter):
    lookup_type = 'exists'

class CharFilter(Filter):
    VALID_LOOKUPS = Filter.VALID_LOOKUPS + transform.STRING_OPERATORS
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
    VALID_LOOKUPS = (None,)
    field_class = fields.ChoiceField

class ObjectIdFilter(Filter):
    field_class = ObjectIdField

class ListFilter(Filter):
    VALID_LOOKUPS = ('in', 'nin', 'all')
    " base filter to compare with list of values "
    field_class = ListField

class AnyFilter(ListFilter):
    " attribute value is in list of provided values "
    lookup_type = 'in'

class NoneFilter(ListFilter):
    " attribute value is not in list of provided values "
    lookup_type = 'nin'

class AllFilter(ListFilter):
    " attribute value contains all of provided values "
    lookup_type = 'all'

class DictFilter(Filter):
    VALID_LOOKUPS = (None,)
    " base filter to compare with dict of values "
    field_class = DictField

class RangeFilter(DictFilter):
    " takes foo.min&foo.max and compares with gte/lte"
    lookup_types = ('gte', 'lte')

    def filter_params(self, value):
        """ return filtering params """
        if value is None:
            return {}

        val_min = value.get('min', None)
        val_max = value.get('max', None)

        target = "__".join(self.field.source_attrs)

        params = {}

        if val_min is not None:
            params[target+"__"+self.lookup_types[0]] = val_min
        if val_max is not None:
            params[target+"__"+self.lookup_types[1]] = val_max

        return params
