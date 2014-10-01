# -*- coding: utf-8 -*-
import logging
from mock import Mock, patch
from requests.packages.urllib3.exceptions import ReadTimeoutError

from django.test import TestCase
from django.core.urlresolvers import reverse

import identity_client

from identity_client.utils import reverse_with_host
from identity_client.tests.test_sso_client import (
    SSOClientRequestToken, SSOClientAccessToken, SSOClientAuthorize
)
from .mock_helpers import patch_request

__all__ = [
    'OAuthCallbackWithoutRequestToken',
    'OAuthCallbackWithRequestToken',
]

from warnings import warn;
warn('decorators.sso_login_required não está testado')
warn('decorators.requires_plan não está testado')

SIDE_EFFECTS = {
    'Timeout': ReadTimeoutError('connection', 'url', "Read timed out. (read timeout=30)"),
    'Memory': MemoryError('KTHXBYE'),
}


class OAuthCallbackWithoutRequestToken(TestCase):

    def test_redirects_to_sso_on_missing_request_token(self):
        self.assertNotIn('request_token', self.client.session)

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                'oauth_verifier': SSOClientAccessToken.VERIFIER
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse_with_host('sso_consumer:request_token'))

    def test_adds_callback_url_to_session(self):
        self.assertNotIn('request_token', self.client.session)

        response = self.client.get(reverse('sso_consumer:callback'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('callback_url', self.client.session)
        self.assertEqual(self.client.session['callback_url'], reverse_with_host('sso_consumer:callback'))

    def test_strips_querystring_before_adding_callback_url_to_session(self):
        self.assertNotIn('request_token', self.client.session)

        response = self.client.get(
            reverse('sso_consumer:callback'), {'key': 'value', 'key2': 'value2'}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('callback_url', self.client.session)
        self.assertEqual(self.client.session['callback_url'], reverse_with_host('sso_consumer:callback'))


class OAuthCallbackWithRequestToken(TestCase):

    def setUp(self):
        with identity_client.tests.use_sso_cassette('fetch_request_token/success'):
            self.client.get(reverse('sso_consumer:request_token'), {})

        self.assertIn('request_token', self.client.session)

    def test_callback_fails_if_service_credentials_are_invalid(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/invalid_credentials'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b"Token request failed with code 401, response was 'Unauthorized consumer with key 'not a valid token''."
        self.assertEqual(response.content, expected)
        self.assertNotIn('access_token', self.client.session)

    def test_callback_fails_if_connection_to_provider_fails(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/500'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b"Token request failed with code 500, response was 'Internal Server Error'."
        self.assertEqual(response.content, expected)
        self.assertNotIn('access_token', self.client.session)

    def test_callback_fails_if_connection_to_provider_times_out(self):
        with patch_request(Mock(side_effect=SIDE_EFFECTS['Timeout'])):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b'connection: Read timed out. (read timeout=30)'
        self.assertEqual(response.content, expected)
        self.assertNotIn('access_token', self.client.session)

    def test_callback_fails_if_provider_is_not_available(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/503'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b"Token request failed with code 503, response was 'Service Unavailable'."
        self.assertEqual(response.content, expected)
        self.assertNotIn('access_token', self.client.session)

    def test_callback_fails_if_request_has_an_error(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/418'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b"Token request failed with code 418, response was 'I'm a Teapot'."
        self.assertEqual(response.content, expected)
        self.assertNotIn('access_token', self.client.session)

    def test_callback_fails_gracefully_when_response_is_malformed(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/malformed_response'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn('access_token', self.client.session)

        content_start = response.content[:72]
        expected_start = b'Could not fetch access token. Unable to decode token from token response'
        self.assertEqual(content_start, expected_start)

        content_end = response.content[-65:]
        expected_end = b'Please ensure the request/response body is x-www-form-urlencoded.'
        self.assertEqual(content_end, expected_end)

    def test_callback_fails_gracefully(self):
        with patch_request(Mock(side_effect=SIDE_EFFECTS['Memory'])):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Could not fetch access token. Unknown error (KTHXBYE)")
        self.assertNotIn('access_token', self.client.session)

    def test_callback_failure_when_verifier_is_invalid(self):
        with identity_client.tests.use_sso_cassette('fetch_access_token/invalid_verifier'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': '56967615'
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b"Token request failed with code 401, response was 'invalid oauth_token verifier: 56967615'."
        self.assertEqual(response.content, expected)
        self.assertNotIn('access_token', self.client.session)

    def test_fails_when_access_token_is_expired(self):
        with identity_client.tests.use_sso_cassette('fetch_user_data/expired_access_token'):
            response = self.client.get(
                reverse('sso_consumer:callback'), {
                    'oauth_token': SSOClientRequestToken.REQUEST_TOKEN['oauth_token'],
                    'oauth_verifier': SSOClientAccessToken.VERIFIER
                }
            )

        self.assertEqual(response.status_code, 503)
        expected = b'Error invoking decorated: 401 Client Error: UNAUTHORIZED ({"detail": "You need to login or otherwise authenticate the request."})'
        self.assertEqual(response.content, expected)
        self.assertEqual(
            self.client.session['access_token'],
            {SSOClientAccessToken.ACCESS_TOKEN['oauth_token']: SSOClientAccessToken.ACCESS_TOKEN['oauth_token_secret']}
        )
