# -*- coding: utf-8 -*-
import logging
import json
import requests
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from identity_client.models import Identity
from identity_client.signals import pre_identity_authentication
from identity_client.decorators import handle_api_exceptions


class MyfcidAPIBackend(object):
    """
    Authenticates a user using the Myfc ID API.
    """
    supports_anonymous_user = False
    supports_inactive_user = False
    supports_object_permissions = False


    def authenticate(self, email=None, password=None, username=None):
        if email and username:
            raise TypeError
        elif username:
            email = username

        identity = None

        # Fetch user data
        status_code, user_data, error = self.fetch_user_data(email, password)

        if user_data:
            logging.info(u'User %s (%s) authenticated', email, user_data['uuid'])
            identity = self.create_local_identity(user_data)
        else:
            logging.info(u'Failed to authenticate user %s', email)

        return identity


    def create_local_identity(self, user_data):
        # Create an updated Identity instance for this user
        identity, created = Identity.objects.get_or_create(uuid=user_data['uuid'])
        self._update_user(identity, user_data)

        # Set this user's backend
        identity.backend = "%s.%s" % (MyfcidAPIBackend.__module__, 'MyfcidAPIBackend')

        # Append additional user data to a temporary attribute
        identity.user_data = user_data

        pre_identity_authentication.send_robust(
            sender='identity_client.MyfcidAPIBackend.backend',
            identity = identity,
            user_data = user_data,
        )
        return identity


    def get_user(self, user_id):
        try:
            user = Identity.objects.get(id=user_id)
        except Exception: # Usuário não existe ou formato do id incorreto (mongodb)
            user = None

        return user


    def _update_user(self, user, user_data):
        user.email = user_data['email']
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.is_active = True
        user.save()


    @handle_api_exceptions
    def fetch_user_data(self, user, password):

        # Build the API uri
        uri = "{0[HOST]}/{0[AUTH_API]}".format(settings.PASSAPORTE_WEB)

        headers = {
            'content-type': 'application/json',
            'cache-control': 'no-cache',
            'user-agent': 'myfc_id client'
        }

        # Request the data
        response = requests.get(uri, auth=(user, password), headers=headers)
        logging.info(
            u'Auth response: status=%s, content=%s',
            response.status_code, response.text
        )

        # If the request is successful, read response data
        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


def get_user(userid=None):
    """
    Returns a User object from an id (User.id). Django's equivalent takes
    request, but taking an id instead leaves it up to the developer to store
    the id in any way they want (session, signed cookie, etc.)
    """
    if not userid:
        return AnonymousUser()
    return MyfcidAPIBackend().get_user(userid) or AnonymousUser()
