from datetime import datetime
from bson import ObjectId, DBRef
from unittest import TestCase
from unittest import mock
from django.http import QueryDict

from mongoengine import Document

from rest_framework import fields
from rest_framework.exceptions import ValidationError

from drf_mongo_filters.fields import ListField, DictField, DateTime000Field, GeoPointField, ObjectIdField, DBRefField


class DateTimeTest(TestCase):
    def test_parse(self):
        fld = DateTime000Field()
        value = fld.to_internal_value("2015-03-03T09:35:00")
        self.assertEqual(value, datetime(2015,3,3,9,35,0,0))

    def test_parse000(self):
        fld = DateTime000Field()
        value = fld.to_internal_value("2015-03-03T09:35:00.123")
        self.assertEqual(value, datetime(2015,3,3,9,35,0,123000))

    def test_parse000000(self):
        fld = DateTime000Field()
        value = fld.to_internal_value("2015-03-03T09:35:00.123456")
        self.assertEqual(value, datetime(2015,3,3,9,35,0,123000))

    def test_convert(self):
        fld = DateTime000Field()
        value = fld.to_internal_value(datetime(2015,3,3,9,35,0,0))
        self.assertEqual(value, datetime(2015,3,3,9,35,0,0))

    def test_convert000(self):
        fld = DateTime000Field()
        value = fld.to_internal_value(datetime(2015,3,3,9,35,0,123000))
        self.assertEqual(value, datetime(2015,3,3,9,35,0,123000))

    def test_convert000(self):
        fld = DateTime000Field()
        value = fld.to_internal_value(datetime(2015,3,3,9,35,0,123456))
        self.assertEqual(value, datetime(2015,3,3,9,35,0,123000))


class RefTests(TestCase):
    def test_oid(self):
        fld = ObjectIdField()
        val = ObjectId()
        value = fld.to_internal_value(str(val))
        self.assertEqual(value, val)

    def test_ref(self):
        fld = DBRefField(collection='doc')
        val = ObjectId()
        value = fld.to_internal_value(str(val))
        self.assertEqual(value, DBRef('doc', val))


class ListFieldTests(TestCase):
    def setUpFld(self, **kwargs):
        fld = ListField(**kwargs)
        fld.bind('foo', mock.Mock())
        return fld

    def test_get_query(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo=1&foo=2&foo=3"))
        self.assertEqual(value, [ "1", "2", "3" ])

    def test_get_data(self):
        fld = self.setUpFld()
        value = fld.get_value({ 'foo': ["1","2","3"] })
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
    def setUpFld(self, **kwargs):
        fld = DictField(**kwargs)
        fld.bind('foo', mock.Mock())
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

    def test_parse_keys_valid(self):
        fld = self.setUpFld(valid_keys=('bar', 'baz'))
        value = fld.to_internal_value({'bar':1, 'baz':1})
        self.assertEqual(value, {'bar': 1, 'baz': 1})

    def test_parse_keys_invalid(self):
        fld = self.setUpFld(valid_keys=('bar', 'baz'))
        with self.assertRaises(ValidationError):
            value = fld.to_internal_value({'bar':1, 'baz':1, 'quz':1})

    def test_parse_keys_required(self):
        fld = self.setUpFld(valid_keys=('bar', 'baz'), required_keys=('bar',))
        value = fld.to_internal_value({'bar':1, 'baz':1})
        self.assertEqual(value, {'bar': 1, 'baz': 1})

    def test_parse_keys_required_missing(self):
        fld = self.setUpFld(valid_keys=('bar', 'baz'), required_keys=('bar',))
        with self.assertRaises(ValidationError):
            value = fld.to_internal_value({'baz':1, 'quz':1})

class GeoPointTests(TestCase):
    def setUpFld(self, **kwargs):
        fld = GeoPointField(**kwargs)
        fld.bind('foo', mock.Mock())
        return fld

    def test_coords(self):
        fld = self.setUpFld()
        value = fld.get_value(QueryDict("foo.lng=60.5&foo.lat=80"))
        value = fld.to_internal_value(value)
        self.assertEqual(value, { 'type': 'Point', 'coordinates': [ 60.5, 80.0 ]})

    def test_inval(self):
        fld = self.setUpFld()
        with self.assertRaises(ValidationError):
            value = fld.get_value(QueryDict("foo.lng=60.5&foo.lat=xxx"))
            value = fld.to_internal_value(value)

    def test_incompl(self):
        fld = self.setUpFld()
        with self.assertRaises(ValidationError):
            value = fld.get_value(QueryDict("foo.lng=60.5"))
            value = fld.to_internal_value(value)
