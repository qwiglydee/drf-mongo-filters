from unittest import TestCase

from rest_framework import fields
from drf_mongo_filters import filters
from drf_mongo_filters.filtersets import Filterset, ModelFilterset

from .models import GeoDoc

class QuerysetTesting():
    def assertQuerysetDocs(self, qs, docs):
        ids = lambda o: o.id
        items = map(ids, qs)
        values = map(ids, docs)
        self.assertEqual(set(items), set(values))

    def assertQuerysetDocsOrdered(self, qs, docs):
        ids = lambda o: o.id
        items = map(ids, qs)
        values = map(ids, docs)
        self.assertEqual(list(items), list(values))

class GeoTests(QuerysetTesting, TestCase):
    def tearDown(self):
        GeoDoc.objects.delete()

    def test_near(self):
        objects = [
            GeoDoc.objects.create(location=(60.0,80.0)),
            GeoDoc.objects.create(location=(61.0,80.0)),
            GeoDoc.objects.create(location=(60.0,81.0)),
            GeoDoc.objects.create(location=(62.0,82.0)),
        ]

        class FS(Filterset):
            foo = filters.GeoNearFilter(source='location')

        fs = FS({'foo': {'lng':60.0, 'lat': 80.0}})
        qs = fs.filter_queryset(GeoDoc.objects.all())
        self.assertQuerysetDocsOrdered(qs, objects)

    def test_near_distance(self):
        objects = [
            GeoDoc.objects.create(location=(54.830956, 83.087933)), #0 ~800m
            GeoDoc.objects.create(location=(54.833693, 83.094477)), #1 ~300m
            GeoDoc.objects.create(location=(54.835314, 83.098243)), #2 0
            GeoDoc.objects.create(location=(54.836246, 83.100283)), #3 ~170m
            GeoDoc.objects.create(location=(54.838594, 83.105564)), #4 ~600m
        ]

        class FS(Filterset):
            loc = filters.GeoNearFilter(source='location')
            dst = filters.GeoDistanceFilter(source='location')

        fs = FS({ 'loc': { 'lng': 54.8353, 'lat': 83.0982 }, 'dst': 500.0 })
        qs = fs.filter_queryset(GeoDoc.objects.all())

        self.assertQuerysetDocsOrdered(qs, [ objects[2], objects[3], objects[1] ])
