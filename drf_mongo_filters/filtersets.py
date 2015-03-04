import copy
from collections import OrderedDict
from rest_framework_mongoengine.utils import get_field_info
from mongoengine import fields

from . import filters

class FiltersetMeta(type):
    """
    Sets _declared_filters
    """
    @classmethod
    def _get_declared_filters(cls, bases, attrs):
        filterlist = [(name, attrs.pop(name))
                   for name, obj in list(attrs.items())
                   if isinstance(obj, filters.Filter)]
        filterlist.sort(key=lambda x: x[1]._creation_order)

        for base in reversed(bases):
            if hasattr(base, '_declared_filters'):
                filterlist = list(base._declared_filters.items()) + filterlist

        return OrderedDict(filterlist)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_filters'] = cls._get_declared_filters(bases, attrs)
        return super(FiltersetMeta, cls).__new__(cls, name, bases, attrs)


class BaseFilterset(metaclass=FiltersetMeta):
    def __init__(self, query=None):
        self.query = query if query else {}

    @property
    def filters(self):
        if not hasattr(self, '_filters'):
            self._filters = self.get_filters()
            for name, flt in self._filters.items():
                flt.bind(name, self)
        return self._filters

    @property
    def values(self):
        if not hasattr(self, '_values'):
            self._values = self.parse_values(self.query)
        return self._values

    def parse_values(self, query):
        """
        extract values from query
        """
        values = {}
        for name, filt in self.filters.items():
            val = filt.parse_value(query)
            if val is None:
                continue
            values[name] = val
        return values

    def filter_queryset(self, queryset):
        """
        convert values to filtering params and apply to queryset
        """
        for name, filt in self.filters.items():
            val= self.values.get(name, None)
            if name is None:
                continue
            params = filt.filter_params(val)
            if not params:
                continue
            queryset = queryset.filter(**params)
        return queryset

class Filterset(BaseFilterset):
    """ declarative queryset

    uses manually declared filters
    """
    def get_filters(self):
        return copy.deepcopy(self._declared_filters)

class ModelFilterset(Filterset):
    """ automagic filterset

    creates filters for some fields of model

    class Meta attrs:
    - model: model to examine
    - fields: model fields to scan
    - exclude: model fields or inherited filters to exclude
    - kwargs: map of customized filter kwargs for each field

    class attr:
    - _filter_mapping: mapping field classes to filter classes
    - _filter_mapping: additionalmappings for custom types
    """
    def get_filters(self):
        declared_filters = copy.deepcopy(self._declared_filters)

        model = getattr(self.Meta, 'model')
        fields = getattr(self.Meta, 'fields', None)
        exclude = getattr(self.Meta, 'exclude', [])
        fltargs = getattr(self.Meta, 'kwargs', {})
        assert not (fields and exclude), "Cannot set both 'fields' and 'exclude'."

        info = get_field_info(model)
        if fields is None:
            fields = list(info.fields.keys())

        filters = {} # unordered
        for name in set(declared_filters.keys()) | set(fields) | set(['id']):
            if name in exclude:
                continue
            if name in declared_filters:
                filters[name] = declared_filters[name]
            else:
                filters[name] = self.filter_for_field(name, info.fields[name], fltargs.get(name,None))

        return filters

    _filter_mapping = {
        fields.StringField: filters.CharFilter,
        fields.URLField: filters.CharFilter,
        fields.EmailField: filters.CharFilter,
        fields.IntField: filters.IntegerFilter,
        fields.LongField: filters.IntegerFilter,
        fields.FloatField: filters.FloatFilter,
        fields.DecimalField: filters.FloatFilter,
        fields.BooleanField: filters.BooleanFilter,
        fields.DateTimeField: filters.DateTimeFilter,
        # fields.ComplexDateTimeField: filters.DateTimeFilter, #### its' a string!
        # fields.EmbeddedDocumentField: filters.Filter,
        fields.ObjectIdField: filters.ObjectIdFilter,
        # fields.GenericEmbeddedDocumentField: filters.Filter,
        # fields.DynamicField: filters.Filter,
        # fields.ListField: filters.Filter,
        # fields.SortedListField: filters.Filter,
        # fields.DictField: filters.Filter,
        # fields.MapField: filters.Filter,
        # fields.ReferenceField: filters.Filter,
        # fields.GenericReferenceField: filters.Filter,
        # fields.BinaryField: filters.Filter,
        # fields.GridFSError: filters.Filter,
        # fields.GridFSProxy: filters.Filter,
        # fields.FileField: filters.Filter,
        # fields.ImageGridFsProxy: filters.Filter,
        # fields.ImproperlyConfigured: filters.Filter,
        # fields.ImageField: filters.Filter,
        # fields.GeoPointField: filters.Filter,
        # fields.PointField: filters.Filter,
        # fields.LineStringField: filters.Filter,
        # fields.PolygonField: filters.Filter,
        # fields.SequenceField: filters.Filter,
        fields.UUIDField: filters.UUIDFilter,
        # fields.GeoJsonBaseField: filters.Filter
    }

    _custom_mapping = {}

    @classmethod
    def find_flt_class(cls, field):
        mapping = {}
        mapping.update(cls._filter_mapping)
        mapping.update(cls._custom_mapping)

        for fld_cls in [field.__class__] + field.__class__.mro():
            if fld_cls in mapping:
                return mapping[fld_cls]

    @classmethod
    def filter_for_field(cls, name, field, args):
        if args is None:
            args = {}

        if isinstance(field, fields.ListField):
            field = field.field

        flt_cls = cls.find_flt_class(field)

        assert flt_cls is not None, (
            'no filter mapping for %(fld_cls)s. please exclude the field, define filter, or adjust %(self_cls)s.filter_mapping' % {
                'fld_cls': str(field.__class__),
                'fld': repr(field),
                'self_cls': str(cls)
            })

        return flt_cls(**args)
