from mongoengine.queryset import transform, Q
from rest_framework import fields

from .fields import  DateTime000Field, ListField, RangeField, GeoPointField,  ObjectIdField

COMPARISION_OPERATORS = ('ne', 'gt', 'gte', 'lt', 'lte')

class Filter():
    """ filter base class
    Wraps serializer field to parse value from querydict.
    Binding name (name of filterset attribute) is used as key in query_params.
    Source of field (defaults to binding name) is used as model attribute to filter.
    Defined in class or provided lookup is used as operator to use for mathing. None (default) is to do not use operator.

    class attrs:
    - field_class: class of serializer field
    - lookup_type: operator to use in queryset filtering, None to use simple comparision
    """
    field_class = fields.Field
    lookup_type = None

    VALID_LOOKUPS = (None,) + COMPARISION_OPERATORS

    # to make skipped fields happy
    partial = True

    _creation_counter = 0
    def __init__(self, lookup=None, name=None, **kwargs):
        """
        Args:
        - lookup: override lookup operator
        - name: override binding name
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

    @property
    def target(self):
        return "__".join(self.field.source_attrs)

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

        key = self.target
        if self.lookup_type is not None:
            key += '__' + self.lookup_type
        return { key: value }

    def __repr__(self):
        return "%s(name='%s',lookup='%s')" % (self.__class__.__qualname__, self.name, self.lookup_type)


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
    field_class = DateTime000Field


class ObjectIdFilter(Filter):
    field_class = ObjectIdField


class ReferenceFilter(ObjectIdFilter):
    field_class = ObjectIdField

    def filter_params(self, value):
        """ return filtering params """
        if value is None:
            return {}
        target = ".".join(self.field.source_attrs)
        return { '__raw__': { target + ".$id": value } }

class ListFilter(Filter):
    " base filter to compare with list of values "
    VALID_LOOKUPS = ('in', 'nin', 'all')
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


class RangeFilter(Filter):
    " takes foo.min&foo.max and compares with gte/lte"
    lookup_types = ('gte', 'lte')
    field_class = RangeField

    def __init__(self, lookup=None, name=None, **kwargs):
        if lookup:
            self.lookup_types = lookup
        super().__init__(name=name, **kwargs)

    def filter_params(self, value):
        """ return filtering params """
        if value is None:
            return {}

        val_min = value.get('min', None)
        val_max = value.get('max', None)
        params = {}

        if val_min == val_max:
            return { self.target: val_min }

        key = self.target + "__"
        if val_min is not None:
            params[key+self.lookup_types[0]] = val_min
        if val_max is not None:
            params[key+self.lookup_types[1]] = val_max

        return params


class IntersectRangeFilter(Filter):
    """ range intersection
    test for intersection of range given in query with range defined by pair of model attrs,
    specified in sources param
    """
    lookup_types = ('gte', 'lte')
    field_class = RangeField

    def __init__(self, sources, name=None, **kwargs):
        self.sources=sources
        super().__init__(name=name, **kwargs)

    @property
    def target(self):
        return self.sources

    def filter_params(self, value):
        if value is None:
            return {}

        val_min = value.get('min', None)
        val_max = value.get('max', None)
        attr_min, attr_max = self.target
        return (Q(**{attr_min:None})|Q(**{attr_min+"__lte": val_max}))&(Q(**{attr_max:None})|Q(**{attr_max+"__gte": val_min}))


class GeoFilter(Filter):
    VALID_LOOKUPS = transform.GEO_OPERATORS

class GeoNearFilter(GeoFilter):
    field_class = GeoPointField
    lookup_type = 'near'

class GeoDistanceFilter(GeoFilter):
    field_class = fields.FloatField
    lookup_type = 'max_distance'
