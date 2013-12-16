# -*- coding: utf-8 -*-
import os
import vcr as vcrpy
import identity_client

__all__ = ['vcr']

cassettes = os.path.join(os.path.dirname(identity_client.__file__), 'tests')
vcr = vcrpy.VCR(
    cassette_library_dir=cassettes, match_on = ['url', 'method', 'headers', 'body']
)
