# -*- coding: utf-8 -*-
from django.conf import settings

class P3PHeaderMiddleware(object):

    def process_response(self, request, response):
        p3p_compact = getattr(settings, 'P3P_COMPACT', None)
        if p3p_compact:
            response['P3P'] = p3p_compact

        return response
