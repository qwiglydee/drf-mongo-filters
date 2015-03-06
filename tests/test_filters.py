from datetime import datetime
from uuid import uuid4
from bson import ObjectId

from unittest import TestCase
from unittest import mock
from django.http import QueryDict
from rest_framework import fields
from rest_framework.exceptions import ValidationError

from drf_mongo_filters.fields import ListField, DictField, DateTime000Field, GeoPointField, ObjectIdField
from drf_mongo_filters.filters import Filter
from drf_mongo_filters import filters

class BaseTests(TestCase):
    def test_creation_order(self):
        flt1 = Filter()
        flt2 = Filter()
        self.assertTrue(flt1._creation_order < flt2._creation_order)

    def test_defaults(self):
        flt = Filter()
        self.assertIsInstance(flt.field, fields.Field)

    def test_fieldclass_redefined(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        self.assertIsInstance(flt.field, fields.CharField)

    def test_field_kwargs(self):
        with mock.patch.object(Filter, 'field_class') as mocked:
            flt = Filter(foo="Foo", bar="Bar")
            mocked.assert_called_once_with(required=False, allow_null=True, foo="Foo", bar="Bar")

    def test_binding(self):
        with mock.patch.object(fields.Field, 'bind') as mocked:
            flt = Filter()
            flt.bind('foo', mock.Mock())
            mocked.assert_called_once_with('foo', flt)

    def test_binding_overrid(self):
        with mock.patch.object(fields.Field, 'bind') as mocked:
            flt = Filter(name='bar')
            flt.bind('foo', mock.Mock())
            mocked.assert_called_once_with('bar', flt)

    def test_parsing(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo=Foo&bar=Bar"))
        self.assertEqual(value, "Foo")

    def test_parsing_missing(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("bar=Bar"))
        self.assertEqual(value, None)

    def test_parsing_empty(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo=&bar=Bar"))
        self.assertEqual(value, None)

    def test_parsing_typed(self):
        class TestFilter(Filter):
            field_class = fields.IntegerField
        flt = TestFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo=123&bar=Bar"))
        self.assertEqual(value, 123)

    def test_parsing_typed_invalid(self):
        class TestFilter(Filter):
            field_class = fields.IntegerField
        flt = TestFilter()
        flt.bind('foo', mock.Mock())
        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx&bar=Bar"))

    def test_params_defaults(self):
        flt = Filter()
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'foo': "Foo"})

    def test_params_given_lookup(self):
        flt = Filter(lookup='gte')
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'foo__gte': "Foo"})

    def test_params_redefined_lookup(self):
        class TestFilter(Filter):
            lookup_type = 'gte'
        flt = TestFilter()
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'foo__gte': "Foo"})

    def test_params_given_name(self):
        flt = Filter(name='fofoo')
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'fofoo': "Foo"})

    def test_params_given_both(self):
        flt = Filter('gte', 'fofoo')
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'fofoo__gte': "Foo"})

    def test_params_given_source(self):
        flt = Filter(source="bar")
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'bar': "Foo"})

    def test_params_given_source_nested(self):
        flt = Filter(source="bar.baz")
        flt.bind('foo', mock.Mock())
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'bar__baz': "Foo"})

class FieldTypesTests(TestCase):
    def setUpFilter(self, flt_class, **kwargs):
        flt = flt_class(**kwargs)
        flt.bind('foo', mock.Mock())
        return flt

    def test_bool(self):
        flt = self.setUpFilter(filters.BooleanFilter)
        self.assertIsInstance(flt.field, fields.NullBooleanField)

        value = flt.parse_value(QueryDict("foo=true"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': True })

        value = flt.parse_value(QueryDict("foo=false"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': False })

    def test_bool_fail(self):
        flt = self.setUpFilter(filters.BooleanFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

    def test_char(self):
        flt = self.setUpFilter(filters.CharFilter)

        value = flt.parse_value(QueryDict("foo=Foo"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': "Foo" })

    def test_uuid(self):
        flt = self.setUpFilter(filters.UUIDFilter)
        val = uuid4()

        value = flt.parse_value(QueryDict("foo=" + str(val)))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': val })

    def test_uuid_fail(self):
        flt = self.setUpFilter(filters.UUIDFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

    def test_int(self):
        flt = self.setUpFilter(filters.IntegerFilter)

        value = flt.parse_value(QueryDict("foo=123"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': 123 })

    def test_int_fail(self):
        flt = self.setUpFilter(filters.IntegerFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=10.5"))
            params = flt.filter_params(value)

    def test_float(self):
        flt = self.setUpFilter(filters.FloatFilter)

        value = flt.parse_value(QueryDict("foo=123"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': 123.0 })

    def test_float_fail(self):
        flt = self.setUpFilter(filters.FloatFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

    def test_datetime(self):
        flt = self.setUpFilter(filters.DateTimeFilter)

        value = flt.parse_value(QueryDict("foo=2015-03-04T09:01"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': datetime(2015,3,4,9,1,0,0) })

        value = flt.parse_value(QueryDict("foo=2015-03-04T09:01:02"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': datetime(2015,3,4,9,1,2,0) })

        value = flt.parse_value(QueryDict("foo=2015-03-04T09:01:02.123"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': datetime(2015,3,4,9,1,2,123000) })

        value = flt.parse_value(QueryDict("foo=2015-03-04T09:01:02.123456"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': datetime(2015,3,4,9,1,2,123000) })

    def test_datetime_fail(self):
        flt = self.setUpFilter(filters.DateTimeFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=2015-03-04"))
            params = flt.filter_params(value)

    def test_date(self):
        flt = self.setUpFilter(filters.DateFilter)
        value = flt.parse_value(QueryDict("foo=2015-03-04"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__gte': datetime(2015,3,4,0,0,0,0),
                                   'foo__lt': datetime(2015,3,5,0,0,0,0) })

    def test_date_fail(self):
        flt = self.setUpFilter(filters.DateFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=2015-03-04T01:02"))
            params = flt.filter_params(value)

    def test_oid(self):
        flt = self.setUpFilter(filters.ObjectIdFilter)
        val = ObjectId()

        value = flt.parse_value(QueryDict("foo=" + str(val)))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': val })

    def test_oid_fail(self):
        flt = self.setUpFilter(filters.ObjectIdFilter)

        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx"))
            params = flt.filter_params(value)

    def test_exists(self):
        flt = self.setUpFilter(filters.ExistsFilter)

        value = flt.parse_value(QueryDict("foo=true"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__exists': True })

        value = flt.parse_value(QueryDict("foo=false"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__exists': False })


class CompoundTests(TestCase):
    def test_any(self):
        flt = filters.AnyFilter()
        flt.bind('foo', mock.Mock())

        value = flt.parse_value(QueryDict("foo=a&foo=b"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__in': ["a","b"] })

    def test_none(self):
        flt = filters.NoneFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo=a&foo=b"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__nin': ["a","b"] })

    def test_all(self):
        flt = filters.AllFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo=a&foo=b"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__all': ["a","b"] })

    def test_range(self):
        flt = filters.RangeFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo.min=a&foo.max=b"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo__gte': "a", 'foo__lte': "b"})

    def test_range_collapse(self):
        flt = filters.RangeFilter()
        flt.bind('foo', mock.Mock())
        value = flt.parse_value(QueryDict("foo.min=a&foo.max=a"))
        params = flt.filter_params(value)
        self.assertEqual(params, { 'foo': "a" })

class GeoTests(TestCase):
    def test_near(self):
        flt = filters.GeoNearFilter()
        flt.bind('foo', mock.Mock())
        self.assertIsInstance(flt.field, GeoPointField)

        value = flt.parse_value(QueryDict("foo.lng=60.0&foo.lat=80"))
        params = flt.filter_params(value)
        self.assertEqual(params, {'foo__near': { 'type': 'Point', 'coordinates': [60.0,80.0] }})

    def test_dist(self):
        flt = filters.GeoDistanceFilter()
        flt.bind('foo', mock.Mock())
        self.assertIsInstance(flt.field, fields.FloatField)
        value = flt.parse_value(QueryDict("foo=1234"))
        params = flt.filter_params(value)
        self.assertEqual(params, {'foo__max_distance': 1234.0})
