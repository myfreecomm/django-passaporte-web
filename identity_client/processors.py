# -*- coding: utf-8 -*-
from django.conf import settings

def hosts(request):
    return {
        'MYFC_ID_HOST': settings.MYFC_ID['HOST'],
        'APPLICATION_HOST': settings.APPLICATION_HOST
    }

