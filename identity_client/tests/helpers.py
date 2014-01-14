# -*- coding: utf-8 -*-
import os
from vcr import VCR                                                                                               

from django.conf import settings                                                                                  
from django.test.client import Client                                                                             
from django.test import TestCase                                                                                  
from django.contrib.auth import authenticate, login                                                               
from django.utils.importlib import import_module                                                                  
from django.http import HttpRequest                                                                               

from identity_client import PERSISTENCE_MODULE                                                                    


__all__ = [
    'MyfcIDTestClient', 'MyfcIDTestCase', 'MyfcIDAPITestCase', 'use_cassette'
]


def use_cassette(*args, **kwargs):
    return VCR(
        cassette_library_dir = os.path.join(os.path.dirname(__file__), 'cassettes', 'api_client'),
        match_on = ['url', 'method', 'headers', 'body'],
        record_mode = 'new_episodes',
    ).use_cassette(*args, **kwargs)


class MyfcIDTestClient(Client):

    def login(self, **credentials):
        """
        Sets the Client to appear as if it has successfully logged into a site.

        Returns True if login is possible; False if the provided credentials
        are incorrect, or the user is inactive, or if the sessions framework is
        not available.
        """
        user = authenticate(**credentials)
        if user:
            engine = import_module(settings.SESSION_ENGINE)

            # Create a fake request to store login details.
            request = HttpRequest()
            if self.session:
                request.session = self.session
            else:
                request.session = engine.SessionStore()
            login(request, user)

            # Save the session values.
            request.session.save()

            # Set the cookie to represent the session.
            session_cookie = settings.SESSION_COOKIE_NAME
            self.cookies[session_cookie] = request.session.session_key
            cookie_data = {
                'max-age': None,
                'path': '/',
                'domain': settings.SESSION_COOKIE_DOMAIN,
                'secure': settings.SESSION_COOKIE_SECURE or None,
                'expires': None,
            }
            self.cookies[session_cookie].update(cookie_data)

            return True
        else:
            return False


class MyfcIDTestCase(PERSISTENCE_MODULE.TestCase):

    userdata = {
        'login' : 'cesar',
        'fullname' : 'Cesar Lustosa',
        'email' : 'cesar@lustosa.net',
        'activation_key': 'Ad6e1161446611529d976dcfb9027eb55',
        'id' : 275310,
        'password': 'e10adc3949ba59abbe56e057f20f883e',
    }

    def __call__(self, result=None):
        """
        Wrapper around default __call__ method to perform common Django test
        set up. This means that user-defined Test Cases aren't required to
        include a call to super().setUp().
        """
        self.client = MyfcIDTestClient()
        try:
            self._pre_setup()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            import sys
            result.addError(self, sys.exc_info())
            return
        super(PERSISTENCE_MODULE.TestCase, self).__call__(result)
        try:
            self._post_teardown()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            import sys
            result.addError(self, sys.exc_info())
            return


class MyfcIDAPITestCase(MyfcIDTestCase):

    http_method = None
    url_name = None
    url = None

    def make_request(self, url, *args, **kwargs):
        client_method = getattr(self.client, self.http_method.lower())
        return client_method(url, *args, **kwargs)


    def test_unauthorized_service(self):
        self.service.acl = []
        self.service.save()

        response = self.make_request(self.url, {},
            HTTP_ACCEPT = 'application/json',
            HTTP_AUTHORIZATION = self.auth,
        )

        self.assertEqual(response.status_code, 403)


    def test_unauthenticated_service(self):

        response = self.make_request(self.url, {},
            HTTP_ACCEPT = 'application/json',
        )

        self.assertEqual(response.status_code, 403)
