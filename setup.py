#!/usr/bin/env python
from distutils.core import setup

setup(
    name='drf-mongo-filters',
    version='2.0.2',
    description="Filtering support for Django Rest Framework Mongoengine.",
    packages=['drf_mongo_filters',],
    url="https://github.com/qwiglydee/drf-mongo-filters",
    download_url="https://github.com/qwiglydee/drf-mongo-filters/releases",
    keywords=['mongoengine', 'django rest framework', 'filtering'],
    author='Maxim Vasiliev',
    author_email='qwiglydee@gmail.com',
    requires=['mongoengine', 'djangorestframework'],
)
