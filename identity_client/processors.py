# -*- coding: utf-8 -*-
from django.conf import settings

def hosts(request):
    return {
        'PASSAPORTE_WEB_HOST': settings.PASSAPORTE_WEB['HOST'],
        'APPLICATION_HOST': settings.APPLICATION_HOST
    }

