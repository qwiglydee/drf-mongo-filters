#!/usr/bin/env python
import sys
from django.conf import settings
from django.core.management import execute_from_command_line
from tests import mongoutils

settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        },
    },
    MONGO_DATABASES={
        'default': {
            'name': 'dumb',
        },
    },
    INSTALLED_APPS=(
        'tests',
    ),
    MIDDLEWARE_CLASSES=(),
    ROOT_URLCONF=None,
    SECRET_KEY='foobar',
    TEST_RUNNER='tests.mongoutils.TestRunner'
)

def runtests():
    mongoutils.mongo_connect()
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    execute_from_command_line(argv)


if __name__ == '__main__':
    runtests()
