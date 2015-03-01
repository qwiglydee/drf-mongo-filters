"""
Expects settings to have:
MONGO_DATABASES {
    'alias' {
         'name': db_name,
         ...other params...
    }
    ...other aliases...
}
"""
from django.conf import settings
from django.test.runner import DiscoverRunner
from mongoengine.connection import connect, disconnect, get_connection

def mongo_connect():
    for alias, params in settings.MONGO_DATABASES.items():
        p = dict(params)
        connect(p.pop('name'), alias=alias, **p)

class TestRunner(DiscoverRunner):
    @classmethod
    def _iter_test_databases(cls):
        for alias, params in settings.MONGO_DATABASES.items():
            test_params = dict(params)
            test_params['name'] = 'test_' + params['name']
            yield (alias, test_params)

    def setup_databases(self, *args, **kwargs):
        for alias, params in self._iter_test_databases():
            disconnect(alias)
            print("Connecting test database for alias '%s': %s" % (alias, params['name']))
            connect(params.pop('name'), alias=alias, **params)
        return super(TestRunner, self).setup_databases(*args, **kwargs)

    def teardown_databases(self, *args, **kwargs):
        for alias, params in self._iter_test_databases():
            connection = get_connection(alias)
            print("Dropping test database for alias '%s': %s" % (alias, params['name']))
            connection.drop_database(params['name'])
            disconnect(alias)
        return super(TestRunner, self).teardown_databases(*args, **kwargs)
