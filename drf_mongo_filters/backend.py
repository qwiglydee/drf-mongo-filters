from rest_framework.filters import BaseFilterBackend
from drf_mongo_filters.filtersets import BaseFilterset, ModelFilterset

class MongoFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_class = getattr(view,'filter_class', None)

        if filter_class is None:
            return queryset

        if not issubclass(filter_class, BaseFilterset):
            raise TypeError("%s expects filter_class to be %s: %s" % (self.__class__.__qualname__, BaseFilterset.__qualname__, repr(filter_class)))

        if not hasattr(view,'get_queryset'):
            raise TypeError("%s expects view to have get_queryset method" % (self.__class__.__qualname__,))

        if issubclass(filter_class, ModelFilterset):
            fs_model = filter_class.Meta.model
            qs_model = view.get_queryset()._document
            if not issubclass(qs_model, fs_model):
                raise TypeError("filter and view document class mismatch: %s vs %s " % (fs_model.__qualname__, qs_model.__qualname__))

        filterset = filter_class(request.query_params)
        return filterset.filter_queryset(queryset)
