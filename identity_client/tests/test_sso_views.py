# -*- coding: utf-8 -*-
import logging
from mock import Mock, patch

from django.utils.importlib import import_module
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

import identity_client

from identity_client.models import Identity
from identity_client.utils import get_account_module
from identity_client.tests.test_sso_client import SSOClientRequestToken
from identity_client.tests.test_decorators import (
    OAuthCallbackWithoutRequestToken,
    OAuthCallbackWithRequestToken,
    SIDE_EFFECTS,
)
from .helpers import full_oauth_dance
from .mock_helpers import patch_request

__all__ = ['InitiateSSO', 'FetchUserData']


class InitiateSSO(TestCase):

    def test_initiate_redirects_user_to_authorization_url_on_success(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 302)
        authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.PASSAPORTE_WEB
        self.assertEqual(
            response['Location'],
            '{0}?oauth_token={1}'.format(authorization_url, SSOClientRequestToken.REQUEST_TOKEN['oauth_token'])
        )

        return

    @patch('logging.error', Mock())
    def test_initiate_adds_oauth_data_to_session_on_success(self):
        expected_token = SSOClientRequestToken.REQUEST_TOKEN['oauth_token']
        expected_token_secret = SSOClientRequestToken.REQUEST_TOKEN['oauth_token_secret']

        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        session = self.client.session
        self.assertTrue('request_token' in session)
        self.assertTrue(expected_token in session['request_token'])
        self.assertEqual(session['request_token'][expected_token], expected_token_secret)

        return

    @patch('logging.error', Mock())
    def test_initiate_fails_if_service_credentials_are_invalid(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/invalid_credentials'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            logging.error.call_args[0][0],
            u"Error invoking initiate: Token request failed with code 401, response was 'Unauthorized consumer with key 'not a valid token''."
        )

    @patch('logging.error', Mock())
    def test_initiate_fails_if_connection_to_provider_fails(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/500'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            logging.error.call_args[0][0],
            u"Error invoking initiate: Token request failed with code 500, response was 'Internal Server Error'."
        )

    @patch('logging.error', Mock())
    def test_initiate_fails_if_connection_to_provider_times_out(self):
        with patch_request(Mock(side_effect=SIDE_EFFECTS['Timeout'])):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(logging.error.call_count, 1)
        self.assertEqual(
            logging.error.call_args[0][0],
            u'Error invoking initiate: connection: Read timed out. (read timeout=30)'
        )

    @patch('logging.error', Mock())
    def test_initiate_fails_if_provider_is_not_available(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/503'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(logging.error.call_count, 1)
        self.assertEqual(
            logging.error.call_args[0][0],
            u"Error invoking initiate: Token request failed with code 503, response was 'Service Unavailable'."
        )

    @patch('logging.error', Mock())
    def test_initiate_fails_if_request_has_an_error(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/418'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(logging.error.call_count, 1)
        self.assertEqual(
            logging.error.call_args[0][0],
            u"Error invoking initiate: Token request failed with code 418, response was 'I'm a Teapot'."
        )

    @patch('logging.error', Mock())
    def test_initiate_fails_gracefully_when_response_is_malformed(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/malformed_response'):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(logging.error.call_count, 1)
        self.assertEqual(
            logging.error.call_args[0][0],
            'Error invoking initiate: Unable to decode token from token response'
        )

    @patch('logging.error', Mock())
    def test_initiate_fails_gracefully(self):
        with patch_request(Mock(side_effect=SIDE_EFFECTS['Memory'])):
            response = self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(logging.error.call_count, 1)
        self.assertEqual(
            logging.error.call_args[0][0] % logging.error.call_args[0][1:],
            u"Error invoking initiate: KTHXBYE {0}".format(type(SIDE_EFFECTS['Memory']))
        )


class FetchUserData(OAuthCallbackWithRequestToken):

    REQUEST_TOKEN = {
        'oauth_token': 'JL0KLSpLpmWHOMwf',
        'oauth_token_secret': 'SoIvesLtE2KuJrNO',
        'oauth_callback_confirmed': 'true',
    }
    ACCESS_TOKEN = {
        'oauth_token_secret': u'pqtkne3xOh838vtJ',
        'oauth_token': u'pSKTtK9DdUrypvyx',
        'oauth_callback_confirmed': u'false'
    }
    VERIFIER = "28583669"

    def _get_real_session(self, client):
        if 'django.contrib.sessions' in settings.INSTALLED_APPS:
            engine = import_module(settings.SESSION_ENGINE)
            cookie = client.cookies.get(settings.SESSION_COOKIE_NAME, None)
            return engine.SessionStore(cookie and cookie.value or None)

    def test_callback_adds_access_token_to_session(self):
        session = self._get_real_session(self.client)
        session['request_token'] = {
            self.REQUEST_TOKEN['oauth_token']: self.REQUEST_TOKEN['oauth_token_secret']
        }
        session.save()

        with identity_client.tests.use_sso_cassette('fetch_user_data/active_request_token'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': FetchUserData.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': FetchUserData.VERIFIER,
                }
            )

        self.assertEqual(response.status_code, 302)

        self.assertIn('access_token', self.client.session)
        self.assertEqual(
            self.client.session['access_token'],
            {self.ACCESS_TOKEN['oauth_token']: self.ACCESS_TOKEN['oauth_token_secret']}
        )

    def test_user_data_is_added_to_session(self):
        response = full_oauth_dance(self.client)
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(self.client.session.get('user_data'), None)

    def test_next_url_is_LOGIN_REDIRECT_URL(self):
        response = full_oauth_dance(self.client)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith(settings.LOGIN_REDIRECT_URL))

    def test_authentication_creates_local_user(self):
        Identity.objects.all().delete()
        response = full_oauth_dance(self.client)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Identity.objects.count(), 1)

    def test_authentication_creates_local_user_accounts(self):
        serviceAccountModel = get_account_module()
        serviceAccountModel.objects.all().delete()
        response = full_oauth_dance(self.client)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(serviceAccountModel.objects.count(), 2)
