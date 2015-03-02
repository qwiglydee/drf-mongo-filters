from rest_framework.filters import BaseFilterBackend
from drf_mongo_filters.filtersets import BaseFilterset

class MongoFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(view)
        if filterset is None:
            return queryset

        values = filterset.parse_values(request.query_params)
        return filterset.filter_queryset(queryset, values)

    def get_filterset(self, view):
        filter_class = getattr(view,'filter_class', None)
        if filter_class is None or not isinstance(filter_class,BaseFilterset):
            return None
        return filter_class()
