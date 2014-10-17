# -*- coding: utf-8 -*-
import logging
from mock import Mock, patch
from requests.packages.urllib3.exceptions import ReadTimeoutError

from django.utils.importlib import import_module
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

import identity_client

from identity_client.utils import reverse_with_host
from identity_client.tests.test_sso_client import (
    SSOClientRequestToken, SSOClientAccessToken, SSOClientAuthorize
)
from .helpers import full_oauth_dance
from .mock_helpers import patch_request

__all__ = [
    'OAuthCallbackWithoutRequestToken',
    'OAuthCallbackWithRequestToken',
    'SSOLoginRequired',
]

from warnings import warn;
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


class SSOLoginRequired(TestCase):

    def test_anonymous_user_is_redirected_to_initiate(self):
        expected_redirect = u'{0}?next={1}'.format(
            reverse_with_host('sso_consumer:request_token'), settings.LOGIN_REDIRECT_URL
        )
        response = self.client.get(settings.LOGIN_REDIRECT_URL, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], expected_redirect)

    def test_requested_url_will_be_used_as_next_url(self):
        requested_url = reverse('alternate_accounts')
        expected_redirect = u'{0}?next={1}'.format(
            reverse_with_host('sso_consumer:request_token'), requested_url
        )
        response = self.client.get(requested_url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], expected_redirect)

    def test_authenticated_user_is_allowed_through(self):
        sso_response = full_oauth_dance(self.client)
        with identity_client.tests.use_sso_cassette('fetch_user_data/active_request_token'):
            first_response = self.client.get(sso_response['Location'])
            requested_url = reverse('alternate_accounts')
            second_response = self.client.get(requested_url, follow=False)

        self.assertEqual(second_response.status_code, 200)
