from unittest import TestCase
from unittest import mock
from django.http import QueryDict
from rest_framework import fields
from rest_framework.exceptions import ValidationError
from rest_framework_mongoengine.fields import ObjectIdField

from drf_mongo_filters.fields import ListField, DictField
from drf_mongo_filters.filters import Filter
from drf_mongo_filters import filters

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


class TypedTests(TestCase):
    def _test_field(self, flt_class, fld_class, **kwargs):
        flt = flt_class(**kwargs)
        self.assertIsInstance(flt.field, fld_class)
        return flt

    def test_Boolean(self):
        self._test_field(filters.BooleanFilter,fields.NullBooleanField)

    def test_Exists(self):
        flt = self._test_field(filters.BooleanFilter,fields.NullBooleanField)
        self.assertEqual(flt.lookup_type, 'exists')

    def test_Char(self):
        self._test_field(filters.CharFilter,fields.CharField)

    def test_UUID(self):
        self._test_field(filters.UUIDFilter,fields.UUIDField)

    def test_Integer(self):
        self._test_field(filters.IntegerFilter,fields.IntegerField)

    def test_Float(self):
        self._test_field(filters.FloatFilter,fields.FloatField)

    def test_DateTime(self):
        self._test_field(filters.DateTimeFilter,fields.DateTimeField)

    def test_Date(self):
        self._test_field(filters.DateFilter,fields.DateField)

    def test_Time(self):
        self._test_field(filters.TimeFilter,fields.TimeField)

    def test_Choice(self):
        self._test_field(filters.ChoiceFilter,fields.ChoiceField,choices=[])

    def test_ObjectId(self):
        self._test_field(filters.ObjectIdFilter, ObjectIdField)

    def test_List(self):
        self._test_field(filters.ListFilter, ListField)

    def test_Any(self):
        fld = self._test_field(filters.AnyFilter, ListField)
        self.assertEqual(fld.lookup_type, 'in')

    def test_None(self):
        fld = self._test_field(filters.NoneFilter, ListField)
        self.assertEqual(fld.lookup_type, 'nin')

    def test_All(self):
        fld = self._test_field(filters.AllFilter, ListField)
        self.assertEqual(fld.lookup_type, 'all')
