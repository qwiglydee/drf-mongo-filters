from rest_framework.filters import BaseFilterBackend
from drf_mongo_filters.filtersets import BaseFilterset

class MongoFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filter_class = getattr(view,'filter_class', None)
        if filter_class is None or not isinstance(filter_class,BaseFilterset):
            return queryset

        filterset = filter_class(request.query_params)
        return filterset.filter_queryset(queryset)

        return filter_class()
