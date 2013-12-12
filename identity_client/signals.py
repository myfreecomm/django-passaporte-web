# -*- coding: utf-8 -*-
import django.dispatch

pre_identity_authentication = django.dispatch.Signal(providing_args=['identity', 'user_data'])
