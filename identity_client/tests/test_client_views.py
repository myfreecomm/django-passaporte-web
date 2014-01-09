# -*- coding: utf-8 -*-
import json

from mock import Mock, patch
import requests

from django.core.urlresolvers import reverse

import identity_client
from identity_client.client_api_methods import APIClient
from identity_client.tests.helpers import MyfcIDTestCase as TestCase


__all__ = ["IdentityRegistrationTest", "IdentityLoginTest"]


test_user_email = 'identity_client@disposableinbox.com'
test_user_password = '*SudN7%r$MiYRa!E'
test_user_uuid = 'c3769912-baa9-4a0c-9856-395a706c7d57'


class IdentityRegistrationTest(TestCase):

    def setUp(self):
        self.registration_data = {
            'first_name': 'Myfc ID',
            'last_name': 'Clients',
            'email': test_user_email,
            'password': test_user_password,
            'password2': test_user_password,
            'tos': True,
        }

        self.url = reverse('registration_register')


    def test_successful_api_registration(self):
        with identity_client.tests.use_cassette('invoke_registration_api/registration_success'):
            response = self.client.post(self.url, self.registration_data)

        self.assertEquals(302, response.status_code)
        self.assertEquals(self.client.session['user_data'], {
            u'first_name': u'Myfc ID',
            u'last_name': u'Clients',
            u'send_partner_news': False,
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57',
            u'is_active': False,
            u'cpf': None,
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'accounts': [],
            u'send_myfreecomm_news': False,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'email': u'identity_client@disposableinbox.com',
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/'
        })


    def test_conflict_error_on_api_registration(self):
        with identity_client.tests.use_cassette('invoke_registration_api/email_already_registered'):
            response = self.client.post(self.url, self.registration_data)

        form = response.context['form']
        self.assertEquals(form.errors, {
            u'field_errors': [u'email'],
            u'email': [u'Este email já está cadastrado. Por favor insira outro email']
        })


    @patch.object(APIClient, 'invoke_registration_api', Mock())
    def test_form_renderization_because_of_empty_fields(self):
        empty_post_data = {'password':'', 'password2':'', 'email':''}
        response = self.client.post(self.url, empty_post_data)
        self.assertFalse(APIClient.invoke_registration_api.called)


class IdentityLoginTest(TestCase):

    def test_successful_login(self):
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            response = self.client.post(
                reverse('auth_login'), {
                    'email': test_user_email,
                    'password': test_user_password,
                }
            )
        self.assertTrue('_auth_user_id' in self.client.session)


    def test_add_userdata_to_session_after_login(self):
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            response = self.client.post(
                reverse('auth_login'), {
                    'email': test_user_email,
                    'password': test_user_password,
                }
            )
        self.assertEquals(self.client.session['user_data'], {
            u'authentication_key': u'$2a$12$nA3ad2y5aSBlg80K9ekbNuvnRO1OI1WUKZyoJqWEhk.PQpD8.6jkS',
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'id_token': u'729dd3a15cf03a80024d0986deee9ae91fdd5d834fabf6f9',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
