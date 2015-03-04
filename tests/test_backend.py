from unittest import TestCase
from unittest import mock
from django.http import QueryDict
from rest_framework.test import APIRequestFactory
from rest_framework.generics import ListAPIView

from drf_mongo_filters.filtersets import Filterset
from drf_mongo_filters.backend import MongoFilterBackend

class BackendTest(TestCase):
    def test_backend(self):
        fs = mock.Mock(spec=Filterset())

        class TestView(ListAPIView):
            filter_backends = (MongoFilterBackend,)
            filter_class = mock.Mock(spec=Filterset, return_value=fs)
            serializer_class = mock.Mock()
            queryset = mock.Mock()

        TestView.as_view()(APIRequestFactory().get("/"))

        TestView.filter_class.assert_called_with({})
        fs.filter_queryset.assert_called_once_with(TestView.queryset)
