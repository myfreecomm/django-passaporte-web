# -*- coding: utf-8 -*-
from django.forms.util import ErrorDict, ErrorList
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django.core.urlresolvers import reverse

def prepare_form_errors(error_dict):
    if 'field_errors' in error_dict:
        error_dict.update(**error_dict['field_errors'])
    return ErrorDict((k, ErrorList(v)) for (k, v) in error_dict.items())


def get_account_module():
    try:
        module_name =  settings.SERVICE_ACCOUNT_MODULE
        app_name, model_name = module_name.split('.')

        models_name = '%s.models' % app_name
        models = __import__(models_name, fromlist=[models_name])

        return getattr(models, model_name)

    except AttributeError:
        return

    except (ValueError, ImportError):
        raise ImproperlyConfigured(
            'settings.SERVICE_ACCOUNT_MODULE: %s could not be imported' % module_name
        )

def reverse_with_host(namespace, *args, **kwargs):
    path = reverse(namespace, *args, **kwargs)
    if path.startswith(settings.APPLICATION_HOST):
        return path
    else:
        return '{0}{1}'.format(settings.APPLICATION_HOST, path)
