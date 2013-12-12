# -*- coding: utf-8 -*-
from mock import Mock, patch

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from identity_client import middleware

enabled_mock = Mock()
enabled_mock.P3P_COMPACT = 'CP=ANY P3P POL ICY'

disabled_mock = Mock()
disabled_mock.P3P_COMPACT = None

class TestP3PMiddleware(TestCase):

    @patch.object(middleware, 'settings', enabled_mock)
    def test_p3p_header_is_added(self):
        response = self.client.get(reverse('auth_login'))
        self.assertTrue('P3P' in response)
        self.assertEquals(response['P3P'], 'CP=ANY P3P POL ICY')


    @patch.object(middleware, 'settings', disabled_mock)
    def test_p3p_header_is_not_added_is_P3P_COMPACT_not_in_settings(self):
        response = self.client.get(reverse('auth_login'))
        self.assertFalse('P3P' in response)
