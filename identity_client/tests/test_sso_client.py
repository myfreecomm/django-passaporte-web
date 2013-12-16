#coding: utf-8
import oauth2 as oauth
from mock import Mock, patch

from django.utils.importlib import import_module
from django.test import TestCase
from django.http import HttpRequest
from django.conf import settings
from mock_helpers import *

from identity_client.sso.client import SSOClient


__all__ = ['SSOClientAuthorize', 'SSOClientRequestToken', 'SSOClientAccessToken']


def create_signed_oauth_request(consumer, sso_client):

    plaintext_signature = oauth.SignatureMethod_PLAINTEXT()

    oauth_request = oauth.Request.from_consumer_and_token(consumer,
                                http_url=sso_client.request_token_url,
                                parameters={'scope':'sso-sample'})

    oauth_request.sign_request(plaintext_signature, consumer, None)

    #XXX: nao sabemos como passar o callback sem hack
    oauth_request['oauth_callback'] = 'http://callback.example.com'

    return oauth_request

def build_access_token_request(oauth_token, oauth_verifier):
    sso_client = SSOClient()

    secret = OAUTH_REQUEST_TOKEN_SECRET
    token = oauth.Token(key=oauth_token, secret=secret)
    token.set_verifier(oauth_verifier)

    consumer = oauth.Consumer(settings.PASSAPORTE_WEB['CONSUMER_TOKEN'],
                               settings.PASSAPORTE_WEB['CONSUMER_SECRET'])
    signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
    oauth_request = oauth.Request.from_consumer_and_token(consumer, token=token,
                 http_url=sso_client.access_token_url, parameters={'scope':'sso-sample'})

    return oauth_request


class SSOClientAuthorize(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    def _get_real_session(self, client):
        if 'django.contrib.sessions' in settings.INSTALLED_APPS:
            engine = import_module(settings.SESSION_ENGINE)
            cookie = client.cookies.get(settings.SESSION_COOKIE_NAME, None)
            return engine.SessionStore(cookie and cookie.value or None)

    @patch.object(SSOClient, 'fetch_request_token', Mock(return_value=oauth.Token(key='key', secret='secret')))
    def test_authorize_invokes_fetch_request_token(self):
        self.sso_client.fetch_request_token.reset_mock()

        request = HttpRequest()
        request.session = self._get_real_session(self.client)
        authorization_url = self.sso_client.authorize(request)

        self.assertTrue(self.sso_client.fetch_request_token.called)
        self.assertEquals(self.sso_client.fetch_request_token.call_count, 1)
        self.assertEquals(self.sso_client.fetch_request_token.call_args, ((), {}))



    @patch.object(SSOClient, 'fetch_request_token', Mock(return_value=oauth.Token(key='key', secret='secret')))
    def test_authorize_stores_request_token_in_session(self):
        self.sso_client.fetch_request_token.reset_mock()

        request = HttpRequest()
        request.session = self._get_real_session(self.client)
        authorization_url = self.sso_client.authorize(request)

        self.assertTrue('request_token' in request.session.keys())
        self.assertEquals(request.session['request_token'], {'key': 'secret'})


    @patch.object(SSOClient, 'fetch_request_token', Mock(return_value=oauth.Token(key='key', secret='secret')))
    def test_authorize_stores_next_url_in_session(self):
        self.sso_client.fetch_request_token.reset_mock()

        request = HttpRequest()
        request.GET = {'next': '/oauth-protected-view/'}
        request.session = self._get_real_session(self.client)
        authorization_url = self.sso_client.authorize(request)

        self.assertTrue('next_url' in request.session.keys())
        self.assertEquals(request.session['next_url'], '/oauth-protected-view/')


class SSOClientRequestToken(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    @patch_httplib2(Mock(return_value=mocked_request_token()))
    def test_fetch_request_token_succeeded(self):
        request_token = self.sso_client.fetch_request_token()

        self.assertEqual(OAUTH_REQUEST_TOKEN, request_token.key)
        self.assertEqual(OAUTH_REQUEST_TOKEN_SECRET, request_token.secret)

    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid token')))
    def test_fetch_request_token_fails_on_invalid_token(self):
        self.assertRaises(
            AssertionError, self.sso_client.fetch_request_token
        )

    @patch_httplib2(Mock(side_effect=AttributeError))
    def test_http_exceptions_are_not_handled(self):
        self.assertRaises(AttributeError, self.sso_client.fetch_request_token)


class SSOClientAccessToken(TestCase):

    def setUp(self):
        self.sso_client = SSOClient()

    @patch_httplib2(Mock(return_value=mocked_access_token()))
    def test_fetch_access_token_succeeded(self):
        access_token = self.sso_client.fetch_access_token()

        self.assertEqual(OAUTH_ACCESS_TOKEN, access_token.key)

    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid verifier')))
    def test_fetch_access_token_fails_on_invalid_verifier(self):
        self.assertRaises(
            AssertionError, self.sso_client.fetch_access_token
        )

    @patch_httplib2(Mock(return_value=mocked_response(401, 'invalid token')))
    def test_fetch_access_token_fails_on_invalid_token(self):
        self.assertRaises(
            AssertionError, self.sso_client.fetch_access_token
        )
