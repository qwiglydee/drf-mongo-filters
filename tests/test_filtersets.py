from collections import OrderedDict
from unittest import TestCase
from unittest import mock
from django.http import QueryDict
from rest_framework.exceptions import ValidationError

from drf_mongo_filters import filters
from drf_mongo_filters.filtersets import Filterset, ModelFilterset

class BaseTests(TestCase):
    def test_declaration(self):
        class TestFS(Filterset):
            foo = filters.CharFilter()
            bar = filters.IntegerFilter()
            baz = filters.BooleanFilter(name='babaz')
        fs = TestFS()

        self.assertEqual(list(fs.filters.keys()), ['foo', 'bar', 'baz'])
        self.assertIsInstance(fs.filters['foo'], filters.CharFilter)
        self.assertIsInstance(fs.filters['bar'], filters.IntegerFilter)
        self.assertIsInstance(fs.filters['baz'], filters.BooleanFilter)

        self.assertEqual([ f.field.source for f in fs.filters.values() ], ['foo', 'bar', 'babaz'])


    def test_inheritance(self):
        class BaseFS(Filterset):
            foo = filters.CharFilter()
            bar = filters.CharFilter()
        class TestFS(BaseFS):
            bar = filters.IntegerFilter(name='babar')
            baz = filters.CharFilter()
        fs = TestFS()

        self.assertEqual(list(fs.filters.keys()), ['foo', 'bar', 'baz'])
        self.assertIsInstance(fs.filters['foo'], filters.CharFilter)
        self.assertIsInstance(fs.filters['bar'], filters.IntegerFilter)
        self.assertIsInstance(fs.filters['baz'], filters.CharFilter)

        self.assertEqual([ f.field.source for f in fs.filters.values() ], ['foo', 'babar', 'baz'])


    def test_parsing(self):
        class TestFS(Filterset):
            foo = filters.CharFilter()
            bar = filters.IntegerFilter(name="babar")
            baz = filters.BooleanFilter()

        fs = TestFS()
        data = QueryDict("foo=Foo&babar=123&baz=true")
        values = fs.parse_values(data)
        self.assertEqual(values, OrderedDict([ ('foo','Foo'), ('bar', 123), ('baz', True) ]))

    def test_parsing_missed(self):
        class TestFS(Filterset):
            foo = filters.CharFilter()
            bar = filters.IntegerFilter()
            baz = filters.BooleanFilter()

        fs = TestFS()
        data = QueryDict("foo=Foo&baz=true")
        values = fs.parse_values(data)
        self.assertEqual(values, OrderedDict([ ('foo','Foo'), ('baz', True) ]))

    def test_parsing_invalid(self):
        class TestFS(Filterset):
            foo = filters.CharFilter()
            bar = filters.IntegerFilter()
            baz = filters.BooleanFilter()

        fs = TestFS()
        data = QueryDict("foo=Foo&bar=xxx&baz=true")
        with self.assertRaises(ValidationError):
            values = fs.parse_values(data)

    def test_filtering(self):
        class TestFS(Filterset):
            foo = filters.CharFilter()
            bar = filters.IntegerFilter(source='babar')
            baz = filters.CharFilter()

        qs = mock.Mock()
        qs.filter = mock.Mock(return_value=qs)
        fs = TestFS()

        fs.filter_queryset(qs, { 'foo': "Foo", 'bar': 123 })

        qs.filter.assert_has_calls([
            mock.call(foo="Foo"),
            mock.call(babar=123)
        ])
