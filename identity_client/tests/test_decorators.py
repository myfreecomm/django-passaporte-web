# -*- coding: utf-8 -*-
from httplib2 import HttpLib2Error
from mock import Mock, patch
from oauth2 import Token

from django.test import TestCase
from django.core.urlresolvers import reverse

from ..utils import reverse_with_host
from mock_helpers import (
    mocked_request_token, mocked_response, mocked_access_token, patch_httplib2, OAUTH_REQUEST_TOKEN
)

__all__ = ['TestOauthCallback', ]

from warnings import warn;
warn('decorators.sso_login_required não está testado')
warn('decorators.requires_plan não está testado')

class TestOauthCallback(TestCase):


    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def _fetch_request_token(self):
        self.client.get(reverse('sso_consumer:request_token'), {})


    def test_redirects_to_sso_on_missing_request_token(self):
        self.assertNotIn('request_token', self.client.session)

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }
        )

        self.assertEquals(response.status_code, 302)

        self.assertEquals(response['Location'], reverse_with_host('sso_consumer:request_token'))


    def test_adds_callback_url_to_session(self):
        self.assertNotIn('request_token', self.client.session)

        response = self.client.get(reverse('sso_consumer:callback'))

        self.assertEquals(response.status_code, 302)

        self.assertIn('callback_url', self.client.session)
        self.assertEquals(
            self.client.session['callback_url'],
            reverse_with_host('sso_consumer:callback')
        )


    def test_strips_querystring_before_adding_callback_url_to_session(self):
        self.assertNotIn('request_token', self.client.session)

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            }
        )

        self.assertEquals(response.status_code, 302)

        self.assertIn('callback_url', self.client.session)
        self.assertEquals(
            self.client.session['callback_url'],
            reverse_with_host('sso_consumer:callback')
        )


    @patch_httplib2(Mock(side_effect=HttpLib2Error))
    def test_fetch_access_token_fails_if_provider_is_down(self):
        self._fetch_request_token()
        self.assertIn('request_token', self.client.session)

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            },
        )

        self.assertEquals(response.status_code, 502)
        self.assertEquals(
            response.content,
            "Could not fetch access token, communication failure:  (<class 'httplib2.HttpLib2Error'>)"
        )

        self.assertNotIn('access_token', self.client.session)


    @patch_httplib2(Mock(side_effect=Exception))
    def test_fetch_access_token_handles_unexpected_errors(self):
        self._fetch_request_token()
        self.assertIn('request_token', self.client.session)

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            },
        )

        self.assertEquals(response.status_code, 500)
        self.assertEquals(
            response.content,
            "Could not fetch access token, unknown error:  (<type 'exceptions.Exception'>)"
        )

        self.assertNotIn('access_token', self.client.session)


    @patch_httplib2(Mock(return_value=mocked_response(200, 'corrupted data')))
    def test_fetch_access_token_fails_on_corrupted_data_returned(self):
        self._fetch_request_token()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            },
        )

        self.assertEquals(response.status_code, 500)
        self.assertEquals(response.content, 'Invalid access token')

        self.assertNotIn('access_token', self.client.session)


    @patch_httplib2(Mock(return_value=mocked_response(400, 'Bad Request')))
    def test_fetch_access_token_handles_response_with_unexpected_status_code(self):
        self._fetch_request_token()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            },
        )

        self.assertEquals(response.status_code, 500)
        self.assertEquals(response.content, 'Could not fetch access token. Response was 400 - Bad Request')

        self.assertNotIn('access_token', self.client.session)


    @patch_httplib2(Mock(return_value=mocked_access_token()))
    @patch('oauth2.Request.sign_request')
    def test_oauth_request_is_correctly_signed(self, sign_request_mock):
        self._fetch_request_token()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            },
        )

        self.assertTrue(isinstance(sign_request_mock.call_args[0][2], Token))


    @patch_httplib2(Mock(return_value=mocked_access_token()))
    def test_adds_access_token_to_session(self):
        self._fetch_request_token()

        response = self.client.get(
            reverse('sso_consumer:callback'), {
                'oauth_token': OAUTH_REQUEST_TOKEN,
                'oauth_verifier': 'niceverifier'
            },
        )

        self.assertIn('access_token', self.client.session)
        self.assertEquals(
            self.client.session['access_token'], {'dummyaccesstoken': 'dummyaccesstokensecret'}
        )
