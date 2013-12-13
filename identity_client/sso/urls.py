# -*- coding: utf-8 -*-
try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *
from django.contrib.auth import views as auth_views

from identity_client.shortcuts import route

urlpatterns = patterns('identity_client.sso.views',
    url(r'^$', 'initiate', name='request_token'),
    url(r'^callback/$', 'fetch_user_data', name='callback'),
    url(r'^iframe/$', 'render_sso_iframe', name='iframe'),
)
