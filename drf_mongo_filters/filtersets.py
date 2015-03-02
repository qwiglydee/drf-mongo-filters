import copy
from collections import OrderedDict
from .filters import Filter

class FiltersetMeta(type):
    """
    Sets _declared_filters
    """
    @classmethod
    def _get_declared_filters(cls, bases, attrs):
        filters = [(name, attrs.pop(name))
                   for name, obj in list(attrs.items())
                   if isinstance(obj, Filter)]
        filters.sort(key=lambda x: x[1]._creation_order)

        for base in reversed(bases):
            if hasattr(base, '_declared_filters'):
                filters = list(base._declared_filters.items()) + filters

        return OrderedDict(filters)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_filters'] = cls._get_declared_filters(bases, attrs)
        return super(FiltersetMeta, cls).__new__(cls, name, bases, attrs)


class BaseFilterset(metaclass=FiltersetMeta):
    @property
    def filters(self):
        if not hasattr(self, '_filters'):
            self._filters = self.get_filters()
            for name, flt in self._filters.items():
                flt.bind(name, self)
        return self._filters

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

    def filter_queryset(self, queryset, values):
        """
        convert values to filtering params and apply to queryset
        """
        for name, filt in self.filters.items():
            val= values.get(name, None)
            if name is None:
                continue
            params = filt.filter_params(val)
            if not params:
                continue
            queryset = queryset.filter(**params)
        return queryset

class Filterset(BaseFilterset):
    """ declarative queryset
    uses only declared filters
    """
    def get_filters(self):
        return copy.deepcopy(self._declared_filters)

class ModelFilterset(Filterset):
    """ automagic filterset
    generates filters for model
    """
    def __init__(self):
        pass

    def get_filters(self):
        declared = copy.deepcopy(self._declared_filters)
