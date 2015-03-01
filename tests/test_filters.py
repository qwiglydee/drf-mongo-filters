from unittest import TestCase
from unittest import mock
from django.http import QueryDict
from rest_framework import fields
from rest_framework.exceptions import ValidationError

from drf_mongo_filters.filters import Filter

class BaseTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fs = mock.Mock()

    def test_creation_order(self):
        flt1 = Filter()
        flt2 = Filter()
        self.assertTrue(flt1._creation_order < flt2._creation_order)

    def test_defaults(self):
        flt = Filter()
        self.assertEqual(flt.lookup_type,'=')
        self.assertIsInstance(flt.field, fields.Field)

    def test_lookup_redefined(self):
        class TestFilter(Filter):
            lookup_type = 'gte'
        flt = TestFilter()
        self.assertEqual(flt.lookup_type,'gte')

    def test_lookup_specified(self):
        flt = Filter(lookup_type='gte')
        self.assertEqual(flt.lookup_type,'gte')

    def test_lookup_specified_invalid(self):
        with self.assertRaises(TypeError):
            flt = Filter(lookup_type='xxx')

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
            flt.bind('foo', self.fs)
            mocked.assert_called_once_with('foo', flt)

    def test_binding_overrid(self):
        with mock.patch.object(fields.Field, 'bind') as mocked:
            flt = Filter(name='bar')
            flt.bind('foo', self.fs)
            mocked.assert_called_once_with('bar', flt)

    def test_parsing(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        flt.bind('foo', self.fs)
        value = flt.parse_value(QueryDict("foo=Foo&bar=Bar"))
        self.assertEqual(value, "Foo")

    def test_parsing_missing(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        flt.bind('foo', self.fs)
        value = flt.parse_value(QueryDict("bar=Bar"))
        self.assertEqual(value, None)

    def test_parsing_empty(self):
        class TestFilter(Filter):
            field_class = fields.CharField
        flt = TestFilter()
        flt.bind('foo', self.fs)
        value = flt.parse_value(QueryDict("foo=&bar=Bar"))
        self.assertEqual(value, None)

    def test_parsing_typed(self):
        class TestFilter(Filter):
            field_class = fields.IntegerField
        flt = TestFilter()
        flt.bind('foo', self.fs)
        value = flt.parse_value(QueryDict("foo=123&bar=Bar"))
        self.assertEqual(value, 123)

    def test_parsing_typed_invalid(self):
        class TestFilter(Filter):
            field_class = fields.IntegerField
        flt = TestFilter()
        flt.bind('foo', self.fs)
        with self.assertRaises(ValidationError):
            value = flt.parse_value(QueryDict("foo=xxx&bar=Bar"))

    def test_params(self):
        flt = Filter()
        flt.bind('foo', self.fs)
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'foo': "Foo"})

    def test_params_lookup(self):
        flt = Filter(lookup_type='gte')
        flt.bind('foo', self.fs)
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'foo__gte': "Foo"})

    def test_params_source(self):
        flt = Filter(source="bar")
        flt.bind('foo', self.fs)
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'bar': "Foo"})

    def test_params_source_nested(self):
        flt = Filter(source="bar.baz")
        flt.bind('foo', self.fs)
        params = flt.filter_params("Foo")
        self.assertEqual(params, { 'bar__baz': "Foo"})
