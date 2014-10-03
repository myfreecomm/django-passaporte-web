# -*- coding: utf-8 -*-
try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *

from django.contrib.auth.views import logout

urlpatterns = patterns('identity_client.views',
    url(r'^sso/', include('identity_client.sso.urls', namespace='sso_consumer')),
    url(r'^logout/$',
        logout,
        {'template_name': 'logout.html'},
        name='auth_logout'
    ),
)
