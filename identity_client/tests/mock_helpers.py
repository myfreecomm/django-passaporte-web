# -*- coding: utf-8 -*-
from mock import Mock, patch

__all__ = ['patch_request']

def patch_request(new):
    return patch('requests.packages.urllib3.connectionpool.HTTPConnectionPool._make_request', new)
