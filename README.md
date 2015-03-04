# drf-mongo-filters
Filtering tools for [django rest framework mongoengine](https://github.com/umutbozkurt/django-rest-framework-mongoengine).
Very similar to [django-filters](https://github.com/alex/django-filter).

## Sinopsis

Declare filters for each query argument and bind it to Filterset:
```python
class SomeFilterset(Filterset):
  foo = filters.CharFilter()
  bar = filters.CharFilter('contains')
```

Apply filters to queryset:
```python
fs = SomeFilterset(QueryDict("foo=Foo&bar=Bar"))
qs = fs.filter_queryset(qs)
# equal to
qs.filter(foo="Foo").filter(bar__contains="Bar")
```

Auto generate filters for each model field with equality comparision:
```python
class SomeFilterset(ModelFilterset):
  class Meta:
    model=SomeDoc
```

Set backend to apply filtering automatically in `GenericAPIView.filter_queryset`, usually called from `ListModelMixin.list`:
```python 
class TestView(ListAPIView):
  filter_backends = (MongoFilterBackend,)
  filter_class = SomeFilterset
```

## Implemented filters
* `BooleanFilter`: parses boolean val using `NullBooleanField`
* `ExistsFilter`: parses boolean, filters with `foo_exists=val`
* `CharFilter`: takes string
* `UUIDFilter`: parses uuid
* `IntegerFilter`: parses int
* `FloatFilter`: parses float
* `DateTimeFilter`: parses datetime using `serializers.DateTimeField`
* `DateFilter`: parses date, filters datetimes with with `gte` and `lte` to match whole day
* `ObjectIdFilter`: parses `bson.ObjectId`
* `ListFilter`: gathers all values with same name; optionally parses with field, specified with argument `child`
* `AnyFilter`: filters with `foo_in=[vals]`
* `NoneFilter`: filters with `foo_nin=[vals]`
* `AllFilter`: filters with `foo_all=[vals]`
* `DictFilter`: gathers all values prefixed with same name; optionally parses with field, specified with argument `child`
* `RangeFilter`: takes `foo.min&foo.max` and flters with `gte` and `lte`
* `GeoNearFilter`: parses geopoint from `foo.lng&foo.lat`, converts to GeoJSON Point and filters with `near` operator
* `GeoDistanceFilter`: parses float and filters with `max_distance` operator

## API

See docstrings for details.

### Filter

###### class
Attributes:
* `field_class`: class used to create serializer field
* `lookup_type`: operator to use for matching

###### Filter(lookup=None, name=None, **kwargs)
Args:
* `lookup`: override matching operator
* `name`: override binding name
* `kwargs`: args to initialize field

### Filterset

###### Filterset(data=None)
Arg:
* `data`: QueryDict or dict containing filtering params

###### filter_queryset(queryset)
Applies all filters to queryset.

### ModelFilterset

###### class
Attribs:
* `_custom_mapping`: mapping of field classes to filter classes to override defaults.

Meta:
* `model`: document definition to examine
* `fields`: restrict fields to given list
* `exclude`: exclude fields from examining
* `kwargs`: mapping of field names to args for filters

