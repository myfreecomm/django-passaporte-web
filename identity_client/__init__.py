# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

__all__ = ['PERSISTENCE_MODULE']

module_name = 'identity_client.%s' % settings.PERSISTENCE_STRATEGY

try:
    PERSISTENCE_MODULE = __import__(
        module_name,
        fromlist=['identity_client']
    )
except ImportError:
    raise ImproperlyConfigured(
        'settings.PERSISTENCE_MODULE: %s could not be imported' % module_name
    )

new_settings = getattr(PERSISTENCE_MODULE, 'settings')
for attr_name in dir(new_settings):
    if not attr_name.isupper():
        continue

    attr_value = getattr(new_settings, attr_name)
    setattr(settings, attr_name, attr_value)

import handlers
