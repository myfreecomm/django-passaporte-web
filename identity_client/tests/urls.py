# -*- coding: utf-8 -*-
from identity_client.urls import *
from django.contrib.auth import views as auth_views

from identity_client.shortcuts import route
from identity_client.views import login, show_login
from identity_client.views import new_identity, register
from identity_client.forms import IdentityAuthenticationForm, RegistrationForm

urlpatterns += patterns('identity_client.views',
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
     url(r'^accounts/$',
        'list_accounts',
        name='list_accounts'
    ),
     url(r'^alternate_accounts/$',
        'list_accounts',
        name='alternate_accounts'
    ),
)
