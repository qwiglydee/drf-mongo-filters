from unittest import TestCase
from unittest import mock
from django.http import QueryDict
from rest_framework.test import APIRequestFactory
from rest_framework.generics import ListAPIView
from mongoengine import Document, fields

from drf_mongo_filters.filtersets import filters, Filterset, ModelFilterset
from drf_mongo_filters.backend import MongoFilterBackend

class Tests(TestCase):
    def test_view(self):
        class TestFilter(Filterset):
            foo = filters.CharFilter()

        class TestView(ListAPIView):
            filter_backends = (MongoFilterBackend,)
            filter_class = TestFilter
            serializer_class = mock.Mock()
            queryset = mock.Mock()

        TestView.as_view()(APIRequestFactory().get("/?foo=Foo"))
        TestView.queryset.filter.assert_called_once_with(foo="Foo")

    def test_unknown_class(self):
        """ filter_class should be our Filterset """
        class Dumb():
            pass

        class TestView(ListAPIView):
            filter_backends = (MongoFilterBackend,)
            filter_class = Dumb
            serializer_class = mock.Mock()
            queryset = mock.Mock()

        with self.assertRaises(TypeError):
            TestView.as_view()(APIRequestFactory().get("/?foo=Foo"))

    def test_model_mismatch(self):
        """ cannot apply filters for one model to queryset from another """
        class FooDoc(Document):
            foo = fields.StringField()

        class BarDoc(Document):
            bar = fields.StringField()

        class FooFilter(ModelFilterset):
            class Meta:
                model = FooDoc

        class BarView(ListAPIView):
            filter_backends = (MongoFilterBackend,)
            filter_class = FooFilter
            serializer_class = mock.Mock()
            queryset = BarDoc.objects

        with self.assertRaises(TypeError):
            BarView.as_view()(APIRequestFactory().get("/?foo=Foo"))

    def test_model_subclassed(self):
        """ can apply filters for base model to queryset of derived """
        class FooDoc(Document):
            meta = { 'allow_inheritance': True}
            foo = fields.StringField()

        class BarDoc(FooDoc):
            bar = fields.StringField()

        class FooFilter(ModelFilterset):
            class Meta:
                model = FooDoc

        class BarView(ListAPIView):
            filter_backends = (MongoFilterBackend,)
            filter_class = FooFilter
            serializer_class = mock.Mock()
            queryset = BarDoc.objects

        BarView.as_view()(APIRequestFactory().get("/?foo=Foo"))
