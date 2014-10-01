# -*- coding: utf-8 -*-
from mock import Mock, patch
from requests_oauthlib.oauth1_session import TokenRequestDenied

from django.utils.importlib import import_module
from django.test import TestCase
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from .mock_helpers import patch_request

import identity_client
from identity_client.sso.client import SSOClient

__all__ = [
    'SSOClientRequestToken',
    'SSOClientAuthorize',
    'SSOClientAccessToken'
]


class SSOClientAuthorize(TestCase):

    AUTHORIZATION_URL = 'https://sandbox.app.passaporteweb.com.br/sso/authorize/?oauth_token=HsLM5nlBdCpARdrt'
    CALLBACK_URL = 'http://127.0.0.1:9000/sso/callback/?oauth_token=HsLM5nlBdCpARdrt&oauth_verifier=56967615'

    def setUp(self):
        self.sso_client = SSOClient()

    def _get_real_session(self, client):
        if 'django.contrib.sessions' in settings.INSTALLED_APPS:
            engine = import_module(settings.SESSION_ENGINE)
            cookie = client.cookies.get(settings.SESSION_COOKIE_NAME, None)
            return engine.SessionStore(cookie and cookie.value or None)

    @patch.object(SSOClient, 'fetch_request_token', Mock(return_value={'oauth_token':'key', 'oauth_token_secret':'secret'}))
    def test_authorize_invokes_fetch_request_token(self):
        self.sso_client.fetch_request_token.reset_mock()

        request = HttpRequest()
        request.session = self._get_real_session(self.client)
        with identity_client.tests.use_sso_cassette('noop'):
            authorization_url = self.sso_client.authorize(request)

        self.assertTrue(self.sso_client.fetch_request_token.called)
        self.assertEquals(self.sso_client.fetch_request_token.call_count, 1)
        self.assertEquals(self.sso_client.fetch_request_token.call_args, ((), {}))

    def test_authorize_stores_request_token_in_session(self):
        request = HttpRequest()
        request.session = self._get_real_session(self.client)
        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            authorization_url = self.sso_client.authorize(request)

        self.assertTrue('request_token' in request.session.keys())
        self.assertEquals(request.session['request_token'], {
            SSOClientRequestToken.REQUEST_TOKEN['oauth_token']: SSOClientRequestToken.REQUEST_TOKEN['oauth_token_secret']
        })

    def test_authorize_stores_next_url_in_session(self):
        request = HttpRequest()
        request.GET = {REDIRECT_FIELD_NAME: '/oauth-protected-view/'}
        request.session = self._get_real_session(self.client)
        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            authorization_url = self.sso_client.authorize(request)

        self.assertTrue(REDIRECT_FIELD_NAME in request.session.keys())
        self.assertEquals(request.session[REDIRECT_FIELD_NAME], '/oauth-protected-view/')

    def test_authorization_url_is_generated_correctly(self):
        request = HttpRequest()
        request.GET = {REDIRECT_FIELD_NAME: '/oauth-protected-view/'}
        request.session = self._get_real_session(self.client)
        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            authorization_url = self.sso_client.authorize(request)

        self.assertEquals(authorization_url, SSOClientAuthorize.AUTHORIZATION_URL)


class SSOClientRequestToken(TestCase):

    REQUEST_TOKEN = {
        'oauth_token': 'HsLM5nlBdCpARdrt',
        'oauth_token_secret': 'OCDrBYT1mY6Y5kV1',
        'oauth_callback_confirmed': 'true',
    }

    def test_fetch_request_token_success(self):
        sso_client = SSOClient()
        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            request_token = sso_client.fetch_request_token()

        self.assertEqual(SSOClientRequestToken.REQUEST_TOKEN, request_token)

    @patch('identity_client.sso.client.settings')
    def test_token_request_is_denied_when_app_credentials_are_invalid(self, settings_mock):
        settings_mock.PASSAPORTE_WEB = {
            'CONSUMER_TOKEN': 'not a valid token',
            'CONSUMER_SECRET': 'not a valid secret',
        }
        sso_client = SSOClient()
        with identity_client.tests.use_sso_cassette('fetch_request_token/invalid_credentials'):
            self.assertRaises(
                TokenRequestDenied, sso_client.fetch_request_token
            )

    def test_malformed_response_generates_ValueError(self):
        sso_client = SSOClient()
        with identity_client.tests.use_sso_cassette('fetch_request_token/malformed_response'):
            self.assertRaises(ValueError, sso_client.fetch_request_token)

    @patch_request(Mock(side_effect=MemoryError))
    def test_abnormal_exceptions_are_not_handled(self):
        sso_client = SSOClient()
        self.assertRaises(MemoryError, sso_client.fetch_request_token)


class SSOClientAccessToken(TestCase):

    VERIFIER = '56967615'
    ACCESS_TOKEN = {
        'oauth_token': 'wT06MCzJYkEVmcLE',
        'oauth_token_secret': 'Xq2U3m3oaKkVfQZ6',
        'oauth_callback_confirmed': 'false',
    }

    def setUp(self):
        self.sso_client = SSOClient(
            resource_owner_key = SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
            resource_owner_secret = SSOClientRequestToken.REQUEST_TOKEN['oauth_token_secret'],
            verifier = SSOClientAccessToken.VERIFIER
        )

    def test_fetch_access_token_success(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/success'):
            access_token = self.sso_client.fetch_access_token()

        self.assertEqual(SSOClientAccessToken.ACCESS_TOKEN, access_token)

    @patch('identity_client.sso.client.settings')
    def test_access_token_request_is_denied_when_app_credentials_are_invalid(self, settings_mock):
        settings_mock.PASSAPORTE_WEB = {
            'CONSUMER_TOKEN': 'not a valid token',
            'CONSUMER_SECRET': 'not a valid secret',
        }
        sso_client = SSOClient(
            resource_owner_key = SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
            resource_owner_secret = SSOClientRequestToken.REQUEST_TOKEN['oauth_token_secret'],
            verifier = SSOClientAccessToken.VERIFIER
        )
        with identity_client.tests.use_sso_cassette('fetch_access_token/invalid_credentials'):
            self.assertRaises(
                TokenRequestDenied, sso_client.fetch_access_token
            )

    def test_access_token_request_is_denied_when_owner_key_is_invalid(self):
        sso_client = SSOClient(
            resource_owner_key = 'invalid owner key',
            resource_owner_secret = SSOClientRequestToken.REQUEST_TOKEN['oauth_token_secret'],
            verifier = SSOClientAccessToken.VERIFIER
        )
        with identity_client.tests.use_sso_cassette('fetch_access_token/invalid_owner_key'):
            self.assertRaises(
                TokenRequestDenied, sso_client.fetch_access_token
            )

    def test_access_token_request_is_denied_when_owner_secret_is_invalid(self):
        sso_client = SSOClient(
            resource_owner_key = SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
            resource_owner_secret = 'invalid owner secret',
            verifier = SSOClientAccessToken.VERIFIER
        )
        with identity_client.tests.use_sso_cassette('fetch_access_token/invalid_owner_secret'):
            self.assertRaises(
                TokenRequestDenied, sso_client.fetch_access_token
            )

    def test_access_token_request_is_denied_when_verifier_is_invalid(self):
        sso_client = SSOClient(
            resource_owner_key = SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
            resource_owner_secret = SSOClientRequestToken.REQUEST_TOKEN['oauth_token_secret'],
            verifier = 'invalid verifier'
        )
        with identity_client.tests.use_sso_cassette('fetch_access_token/invalid_verifier'):
            self.assertRaises(
                TokenRequestDenied, sso_client.fetch_access_token
            )

    def test_malformed_response_generates_ValueError(self):
        sso_client = SSOClient()
        with identity_client.tests.use_sso_cassette('fetch_access_token/malformed_response'):
            self.assertRaises(ValueError, sso_client.fetch_access_token)

    @patch_request(Mock(side_effect=MemoryError))
    def test_abnormal_exceptions_are_not_handled(self):
        self.assertRaises(MemoryError, self.sso_client.fetch_access_token)
