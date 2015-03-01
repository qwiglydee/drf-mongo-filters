from unittest import TestCase
from unittest import mock
from django.http import QueryDict

from rest_framework import fields
from rest_framework.exceptions import ValidationError

from drf_mongo_filters.fields import ListField, DictField

class ListFieldTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fs = mock.Mock()
        cls.fs.parent = None

    def setUpFld(self, **kwargs):
        fld = ListField(**kwargs)
        fld.bind('foo', self.fs)
        return fld

    def test_get(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo=1&foo=2&foo=3"))
        self.assertEqual(value, [ "1", "2", "3" ])

    def test_get_empty(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo="))
        self.assertEqual(value, fields.empty)

    def test_get_missing(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict(""))
        self.assertEqual(value, fields.empty)

    def test_parse_default(self):
        fld = self.setUpFld()
        value = fld.to_internal_value([ "1", "2", "3" ])
        self.assertEqual(value, [ "1", "2", "3" ])

    def test_parse_typed(self):
        fld = self.setUpFld(child=fields.IntegerField())
        value = fld.to_internal_value([ "1", "2", "3" ])
        self.assertEqual(value, [ 1, 2, 3 ])

    def test_parse_typed_invalid(self):
        fld = self.setUpFld(child=fields.IntegerField())
        with self.assertRaises(ValidationError):
            value = fld.to_internal_value([ "1", "xxx", "3" ])

class DictFieldTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fs = mock.Mock()
        cls.fs.parent = None

    def setUpFld(self, **kwargs):
        fld = DictField(**kwargs)
        fld.bind('foo', self.fs)
        return fld

    def test_get(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo.aa=1&foo.bb=2&foo.cc=3"))
        self.assertEqual(value, { 'aa': "1", 'bb':"2", 'cc':"3" })

    def test_get_empty(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo="))
        self.assertEqual(value, fields.empty)

    def test_get_missing(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict(""))
        self.assertEqual(value, fields.empty)

    def test_get_empty_sub(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo.aa=1&foo.bb=&foo.cc="))
        self.assertEqual(value, { 'aa': "1" })

    def test_get_empty_all(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo.aa=&foo.bb=&foo.cc="))
        self.assertEqual(value, fields.empty)

    def test_parse_default(self):
        fld = self.setUpFld()
        value = fld.to_internal_value({ 'aa': "1", 'bb':"2", 'cc':"3" })
        self.assertEqual(value, { 'aa': "1", 'bb':"2", 'cc':"3" })

    def test_parse_typed(self):
        fld = self.setUpFld(child=fields.IntegerField())
        value = fld.to_internal_value({ 'aa': "1", 'bb':"2", 'cc':"3" })
        self.assertEqual(value, { 'aa': 1, 'bb':2, 'cc':3 })

    def test_parse_typed_invalid(self):
        fld = self.setUpFld(child=fields.IntegerField())
        with self.assertRaises(ValidationError):
            value = fld.to_internal_value({ 'aa': "1", 'bb':"xxx", 'cc':"3" })
