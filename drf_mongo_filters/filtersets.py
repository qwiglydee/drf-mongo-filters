import copy
from collections import OrderedDict
from mongoengine import fields as mongo_fields
from mongoengine.queryset.visitor import QNode

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
            val = self.values.get(name, None)
            if name is None:
                continue
            params = filt.filter_params(val)
            if not params:
                continue
            if isinstance(params, dict):
                queryset = queryset.filter(**params)
            if isinstance(params, QNode):
                queryset = queryset.filter(params)
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

        if fields is None:
            fields = model._fields_ordered

        docfilters = {} # unordered
        for name in set(declared_filters.keys()) | set(fields) | set(['id']):
            if name in exclude:
                continue
            if name in declared_filters:
                docfilters[name] = declared_filters[name]
            else:
                docfilters[name] = self.filter_for_field(name, model._fields[name], fltargs.get(name,None))

        return docfilters

    default_filters_mapping = {
        mongo_fields.StringField: filters.CharFilter,
        mongo_fields.URLField: filters.CharFilter,
        mongo_fields.EmailField: filters.CharFilter,
        mongo_fields.IntField: filters.IntegerFilter,
        mongo_fields.LongField: filters.IntegerFilter,
        mongo_fields.FloatField: filters.FloatFilter,
        mongo_fields.DecimalField: filters.FloatFilter,
        mongo_fields.BooleanField: filters.BooleanFilter,
        mongo_fields.DateTimeField: filters.DateTimeFilter,
        # mongo_fields.ComplexDateTimeField: filters.DateTimeFilter, #### its' a string!
        # mongo_fields.EmbeddedDocumentField: filters.Filter,
        mongo_fields.ObjectIdField: filters.ObjectIdFilter,
        mongo_fields.ReferenceField: filters.ReferenceFilter,
        # mongo_fields.GenericEmbeddedDocumentField: filters.Filter,
        # mongo_fields.DynamicField: filters.Filter,
        # mongo_fields.ListField: filters.Filter,
        # mongo_fields.SortedListField: filters.Filter,
        # mongo_fields.DictField: filters.Filter,
        # mongo_fields.MapField: filters.Filter,
        # mongo_fields.GenericReferenceField: filters.Filter,
        # mongo_fields.BinaryField: filters.Filter,
        # mongo_fields.GridFSError: filters.Filter,
        # mongo_fields.GridFSProxy: filters.Filter,
        # mongo_fields.FileField: filters.Filter,
        # mongo_fields.ImageGridFsProxy: filters.Filter,
        # mongo_fields.ImproperlyConfigured: filters.Filter,
        # mongo_fields.ImageField: filters.Filter,
        # mongo_fields.GeoPointField: filters.Filter,
        # mongo_fields.PointField: filters.Filter,
        # mongo_fields.LineStringField: filters.Filter,
        # mongo_fields.PolygonField: filters.Filter,
        # mongo_fields.SequenceField: filters.Filter,
        mongo_fields.UUIDField: filters.UUIDFilter,
        # mongo_fields.GeoJsonBaseField: filters.Filter
    }

    filters_mapping = {}

    @classmethod
    def find_flt_class(cls, field):
        mapping = {}
        mapping.update(cls.default_filters_mapping)
        mapping.update(cls.filters_mapping)

        for fld_cls in [field.__class__] + field.__class__.mro():
            if fld_cls in mapping:
                return mapping[fld_cls]

    @classmethod
    def filter_for_field(cls, name, field, args):
        if args is None:
            args = {}

        if isinstance(field, mongo_fields.ListField):
            field = field.field

        flt_cls = cls.find_flt_class(field)

        assert flt_cls is not None, (
            'no filter mapping for %(fld_cls)s %(fld_name)s. please exclude the field, define filter, or adjust %(self_cls)s.filter_mapping' % {
                'fld_cls': str(field.__class__),
                'fld_name': name,
                'fld': repr(field),
                'self_cls': str(cls)
            })

        return flt_cls(**args)
