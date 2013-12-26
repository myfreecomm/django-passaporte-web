# -*- coding: utf-8 -*-
try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *

from django.contrib.auth import views as auth_views

from shortcuts import route
from views import login, show_login
from views import new_identity, register
from forms import IdentityAuthenticationForm, RegistrationForm

urlpatterns = patterns('identity_client.views',
    route(r'^registration/',
        GET=new_identity,
        POST=register,
        kwargs={'registration_form': RegistrationForm},
        name='registration_register'
    ),
    route(r'^login/$',
        GET=show_login,
        POST=login,
        kwargs={'authentication_form': IdentityAuthenticationForm},
        name='auth_login'
    ),
     url(r'^logout/$',
        auth_views.logout,
        {'template_name': 'logout.html'},
        name='auth_logout'
    ),
     url(r'^accounts/$',
        'list_accounts',
        name='list_accounts'
    ),
    (r'^sso/', include('identity_client.sso.urls', namespace='sso_consumer')),
)
