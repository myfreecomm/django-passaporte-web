# -*- encoding: utf-8 -*-
from django.http import Http404
try:
    from django.conf.urls.defaults import url
except ImportError:
    from django.conf.urls import url


def route_by_method(request, *args, **kwargs):
    valid_methods = ('GET', 'POST', 'PUT', 'DELETE')

    method_views = dict(
        (k, v) for k, v in kwargs.items() if k in valid_methods
    )

    try:
        requested_view = method_views[request.method]
        return requested_view(request, *args, **kwargs)
    except KeyError:
        raise Http404


def route(regex, GET=None, POST=None, PUT=None, DELETE=None, kwargs=None, name=None, prefix=''):
    kwargs = kwargs or {}

    kwargs.update({
        'GET': GET,
        'POST': POST,
        'PUT': PUT,
        'DELETE': DELETE
    })

    return url(regex, route_by_method, kwargs, name, prefix)
