#coding: utf-8
from django.test.simple import *

from mongoengine import connection

__all__ = ['MongoEngineTestCase']

class MongoEngineTestCase(TestCase):
    """
    TestCase class that clear the collection between the tests
    """
    def __init__(self, methodName='runtest'):
        self.db = connection._get_db()
        super(MongoEngineTestCase, self).__init__(methodName)

    def _post_teardown(self):
        super(MongoEngineTestCase, self)._post_teardown()
        for collection in self.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)
