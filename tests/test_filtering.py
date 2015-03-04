from unittest import TestCase
from datetime import datetime, timedelta
from uuid import uuid4
from bson import ObjectId

from rest_framework import fields
from drf_mongo_filters import filters
from drf_mongo_filters.filtersets import Filterset, ModelFilterset

from .models import SimpleDoc, DeepDoc, EmbDoc

class QuerysetTesting():
    def assertQuerysetDocs(self, qs, docs):
        ids = lambda o: o.id
        items = map(ids, qs)
        values = map(ids, docs)
        self.assertEqual(set(items), set(values))

class BasicTests(QuerysetTesting, TestCase):
    def tearDown(self):
        SimpleDoc.objects.delete()

    def test_bool(self):
        objects = [
            SimpleDoc.objects.create(f_bool=True),
            SimpleDoc.objects.create(f_bool=False),
            SimpleDoc.objects.create()
        ]

        class FS(Filterset):
            foo = filters.BooleanFilter(source='f_bool')

        fs = FS({'foo': True})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[0:1])

        fs = FS({'foo': False})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:2])

    def test_exists(self):
        objects = [
            SimpleDoc.objects.create(),
            SimpleDoc.objects.create(f_int=1),
            SimpleDoc.objects.create(f_int=2),
        ]

        class FS(Filterset):
            foo = filters.ExistsFilter(source='f_int')

        fs = FS({'foo': True})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:])

        fs = FS({'foo': False})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[0:1])

    def test_str(self):
        objects = [
            SimpleDoc.objects.create(f_str="foofoo"),
            SimpleDoc.objects.create(f_str="foobar"),
            SimpleDoc.objects.create(f_str="barbaz")
        ]

        class FS(Filterset):
            foo = filters.CharFilter('contains', source='f_str')

        fs = FS({'foo': "foo"})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[0:2])

        fs = FS({'foo': "bar"})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:3])


    def test_uuid(self):
        objects = [
            SimpleDoc.objects.create(f_uuid=uuid4()),
            SimpleDoc.objects.create(f_uuid=uuid4()),
            SimpleDoc.objects.create(f_uuid=uuid4()),
        ]

        class FS(Filterset):
            foo = filters.UUIDFilter(source='f_uuid')

        fs = FS({'foo': str(objects[1].f_uuid)})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:2])

    def test_int(self):
        objects = [
            SimpleDoc.objects.create(f_int=10),
            SimpleDoc.objects.create(f_int=20),
            SimpleDoc.objects.create(f_int=30),
        ]

        class FS(Filterset):
            foo = filters.IntegerFilter('gte', source='f_int')
            bar = filters.IntegerFilter('lte', source='f_int')

        fs = FS({'foo': 20})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:3])

        fs = FS({'bar': 20})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[0:2])

        fs = FS({'foo':20, 'bar': 20})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:2])

    def test_flt(self):
        objects = [
            SimpleDoc.objects.create(f_flt=0.10),
            SimpleDoc.objects.create(f_flt=0.20),
            SimpleDoc.objects.create(f_flt=0.30),
        ]

        class FS(Filterset):
            foo = filters.FloatFilter('gte', source='f_flt')
            bar = filters.FloatFilter('lte', source='f_flt')

        fs = FS({'foo': 0.2})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:3])

        fs = FS({'bar': 0.2})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[0:2])

        fs = FS({'foo': 0.2, 'bar': 0.2})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:2])

    def test_datetime(self):
        d0 = datetime.utcnow()
        dl = timedelta(milliseconds=1)
        d1 = d0 + dl
        d2 = d1 + dl
        d3 = d2 + dl

        objects = [
            SimpleDoc.objects.create(f_dt=d1),
            SimpleDoc.objects.create(f_dt=d2),
            SimpleDoc.objects.create(f_dt=d3),
        ]

        class FS(Filterset):
            dt = filters.DateTimeFilter(source='f_dt')
            dt_gt = filters.DateTimeFilter('gte', source='f_dt')
            dt_gte = filters.DateTimeFilter('gte', source='f_dt')

        fs = FS({'dt': d2})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:2])

        fs = FS({'dt_gt': d2})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:3])

        fs = FS({'dt_gte': d2})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:3])

    def test_oid(self):
        oid = ObjectId()
        objects = [
            SimpleDoc.objects.create(f_oid=ObjectId()),
            SimpleDoc.objects.create(f_oid=oid),
            SimpleDoc.objects.create(f_oid=ObjectId()),
        ]

        class FS(Filterset):
            foo = filters.CharFilter(source='f_oid')

        fs = FS({'foo': oid})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:2])

    def test_uuid(self):
        uuid = uuid4()
        objects = [
            SimpleDoc.objects.create(f_uuid=uuid4()),
            SimpleDoc.objects.create(f_uuid=uuid),
            SimpleDoc.objects.create(f_uuid=uuid4()),
        ]

        class FS(Filterset):
            foo = filters.CharFilter(source='f_uuid')

        fs = FS({'foo': uuid})
        qs = fs.filter_queryset(SimpleDoc.objects.all())


class CompoundTests(QuerysetTesting, TestCase):
    def tearDown(self):
        SimpleDoc.objects.delete()
        DeepDoc.objects.delete()

    def test_list(self):
        objects = [
            SimpleDoc.objects.create(f_str="foo"),
            SimpleDoc.objects.create(f_str="bar"),
            SimpleDoc.objects.create(f_str="baz")
        ]

        class FS(Filterset):
            foo = filters.AnyFilter(source='f_str')
            bar = filters.NoneFilter(source='f_str')

        fs = FS({'foo': ["bar","baz"]})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:3])

        fs = FS({'bar': ["bar","baz"]})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[0:1])

    def test_None(self):
        objects = [
            DeepDoc.objects.create(f_list=[1,2]),
            DeepDoc.objects.create(f_list=[2,3]),
            DeepDoc.objects.create(f_list=[3,4]),
        ]

        class FS(Filterset):
            foo = filters.NoneFilter(source='f_list')

        fs = FS({'foo': [1,2]})
        qs = fs.filter_queryset(DeepDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[2:3])

    def test_range(self):
        objects = [
            SimpleDoc.objects.create(f_int=3),
            SimpleDoc.objects.create(f_int=5),
            SimpleDoc.objects.create(f_int=7),
            SimpleDoc.objects.create(f_int=11),
            SimpleDoc.objects.create(f_int=13),
        ]

        class FS(Filterset):
            foo = filters.RangeFilter(child=fields.IntegerField(), source='f_int')
            bar = filters.RangeFilter(child=fields.IntegerField(), lookup=('gt','lt'), source='f_int')

        fs = FS({'foo': {'min':5, 'max':11}})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:4])

        fs = FS({'bar': {'min':5, 'max':11}})
        qs = fs.filter_queryset(SimpleDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[2:3])


class DeepFieldsTests(QuerysetTesting, TestCase):
    def tearDown(self):
        DeepDoc.objects.delete()

    def test_list(self):
        objects = [
            DeepDoc.objects.create(f_list=[10,11]),
            DeepDoc.objects.create(f_list=[20,21]),
            DeepDoc.objects.create(f_list=[30,31]),
        ]
        class FS(Filterset):
            foo = filters.IntegerFilter('gte', source='f_list')
        fs = FS({'foo': "20"})
        qs = fs.filter_queryset(DeepDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:])

    def test_dict(self):
        objects = [
            DeepDoc.objects.create(f_dict={'foo':"foo1", 'bar':"bar1"}),
            DeepDoc.objects.create(f_dict={'foo':"foo2", 'bar':"bar2"}),
            DeepDoc.objects.create(f_dict={'foo':"foo3", 'bar':"bar3"})
        ]
        class FS(Filterset):
            foo = filters.CharFilter('gte', source='f_dict.foo')
        fs = FS({'foo': "foo2"})
        qs = fs.filter_queryset(DeepDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:])

    def test_map(self):
        objects = [
            DeepDoc.objects.create(f_map={'foo':1, 'bar':1}),
            DeepDoc.objects.create(f_map={'foo':2, 'bar':2}),
            DeepDoc.objects.create(f_map={'foo':3, 'bar':3})
        ]
        class FS(Filterset):
            foo = filters.IntegerFilter('gte', source='f_map.foo')
        fs = FS({'foo': "2"})
        qs = fs.filter_queryset(DeepDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:])

    def test_emb(self):
        objects = [
            DeepDoc.objects.create(f_emb=EmbDoc(foo="foo1", bar="bar1")),
            DeepDoc.objects.create(f_emb=EmbDoc(foo="foo2", bar="bar2")),
            DeepDoc.objects.create(f_emb=EmbDoc(foo="foo3", bar="bar3")),
        ]
        class FS(Filterset):
            foo = filters.CharFilter('gte', source='f_emb.foo')
        fs = FS({'foo': "foo2"})
        qs = fs.filter_queryset(DeepDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:])

    def test_emblist(self):
        objects = [
            DeepDoc.objects.create(f_emblist=[EmbDoc(foo="foo10", bar="bar10"),EmbDoc(foo="foo11", bar="bar11")]),
            DeepDoc.objects.create(f_emblist=[EmbDoc(foo="foo20", bar="bar20"),EmbDoc(foo="foo21", bar="bar21")]),
            DeepDoc.objects.create(f_emblist=[EmbDoc(foo="foo30", bar="bar30"),EmbDoc(foo="foo31", bar="bar31")]),
        ]
        class FS(Filterset):
            foo = filters.CharFilter('gte', source='f_emblist.foo')
        fs = FS({'foo': "foo20"})
        qs = fs.filter_queryset(DeepDoc.objects.all())
        self.assertQuerysetDocs(qs, objects[1:])
