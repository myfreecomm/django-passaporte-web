# -*- coding: utf-8 -*-
try:
    import mongoengine
except ImportError:
    import sys
    message = u"ERRO: Você precisa instalar o pacote 'mongoengine' para utilizar esta estratégia de persistência\n"
    sys.stdout.write(message.encode('utf-8'))
    sys.exit(1)

from django.conf import settings as django_settings
from django.test import TestCase as SimpleTestCase

import models
import settings

__all__ = ['models', 'settings', 'TestCase']


mongoengine.connect(
    django_settings.NOSQL_DATABASES['NAME'],
    host=django_settings.NOSQL_DATABASES['HOST']
)


class TestCase(SimpleTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    def __init__(self, methodName='runtest'):
        self.db = mongoengine.connection._get_db()
        super(TestCase, self).__init__(methodName)

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        for collection in self.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)

    def _fixture_teardown(self, *args, **kwargs):
        pass
