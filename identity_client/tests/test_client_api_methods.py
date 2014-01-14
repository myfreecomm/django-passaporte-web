# -*- coding: utf-8 -*-
from datetime import datetime, date
import time

from mock import patch

from django.conf import settings
from django.test import TestCase

import identity_client
from identity_client.client_api_methods import APIClient
from identity_client.forms import RegistrationForm, IdentityInformationForm

__all__ = [
    'InvokeRegistrationApi',
    'FetchIdentityData', 'FetchIdentityDataWithEmail',
    'UpdateUserApi',
    'FetchAssociationData', 'UpdateAssociationData',
    'FetchUserAccounts',
    'FetchAccountData',
    'CreateUserAccount', 'CreateUserAccountWithUUID',
    'UpdateAccountData',
    'AddAccountMember', 'UpdateMemberRoles', 'RemoveAccountMember'
]

test_user_email = 'identity_client@disposableinbox.com'
test_user_password = '*SudN7%r$MiYRa!E'
test_user_uuid = 'c3769912-baa9-4a0c-9856-395a706c7d57'
test_account_uuid = 'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
second_account_uuid = 'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
second_user_email = 'identity_client_2@disposableinbox.com'
second_user_uuid = 'bedcd531-c741-4d32-90d7-a7f7432f3f15'


class InvokeRegistrationApi(TestCase):

    def setUp(self):
        self.registration_data = {
            'first_name': 'Myfc ID',
            'last_name': 'Clients',
            'email': test_user_email,
            'password': test_user_password,
            'password2': test_user_password,
            'tos': True,
            'next': 'anything. will be ignored',
        }

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        response = APIClient.invoke_registration_api(form)
        status_code, content, new_form = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.']
        })

    def test_request_with_wrong_credentials(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('invoke_registration_api/wrong_credentials'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.']
        })

    def test_request_with_application_without_permissions(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())

        with identity_client.tests.use_cassette('invoke_registration_api/application_without_permissions'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Erro no servidor. Entre em contato com o suporte.']
        })

    def test_request_without_tos_set(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        del(form.cleaned_data['tos'])

        with identity_client.tests.use_cassette('invoke_registration_api/without_tos_set'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'tos': [u'Você precisa concordar com os Termos de Serviço']
        })

    def test_request_with_password_only_once(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        del(form.cleaned_data['password2'])

        with identity_client.tests.use_cassette('invoke_registration_api/with_password_only_once'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'password2': [u'Este campo é obrigatório.']
        })

    def test_request_with_passwords_not_matching(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        form.cleaned_data['password2'] = 'will not match'

        with identity_client.tests.use_cassette('invoke_registration_api/with_passwords_not_matching'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'__all__': [u"The two password fields didn't match."]
        })

    def test_registration_success(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())

        with identity_client.tests.use_cassette('invoke_registration_api/registration_success'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
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
        self.assertEquals(form.errors, {})

    def test_email_already_registered(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())

        with identity_client.tests.use_cassette('invoke_registration_api/email_already_registered'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 409)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'field_errors': [u'email'],
            u'email': [u'Este email já está cadastrado. Por favor insira outro email']
        })

    def test_cpf_already_registered(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        form.cleaned_data['email'] = 'identity_client+1@disposableinbox.com'
        form.cleaned_data['cpf'] = '11111111111'

        with identity_client.tests.use_cassette('invoke_registration_api/cpf_already_registered'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Este número de CPF já está cadastrado.']
        })

    def test_invalid_cpf_pt1(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        form.cleaned_data['email'] = 'identity_client+1@disposableinbox.com'
        form.cleaned_data['cpf'] = '1111111111122222222'

        with identity_client.tests.use_cassette('invoke_registration_api/invalid_cpf_pt1'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 19).']
        })

    def test_invalid_cpf_pt2(self):
        form = RegistrationForm(self.registration_data)
        self.assertTrue(form.is_valid())
        form.cleaned_data['email'] = 'identity_client+1@disposableinbox.com'
        form.cleaned_data['cpf'] = 'asdfgqwertzxcvb'

        with identity_client.tests.use_cassette('invoke_registration_api/invalid_cpf_pt2'):
            response = APIClient.invoke_registration_api(form)
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 15).']
        })


class FetchIdentityData(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_identity_data(uuid=test_user_uuid)
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('fetch_identity_data/wrong_credentials'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 401, 'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):

        with identity_client.tests.use_cassette('fetch_identity_data/application_without_permissions'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': 403, 'message': '403 Client Error: FORBIDDEN'})

    def test_request_with_uuid_which_does_not_exist(self):

        with identity_client.tests.use_cassette('fetch_identity_data/uuid_which_does_not_exist'):
            response = APIClient.fetch_identity_data(uuid='00000000-0000-0000-0000-000000000000')
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"',
            'status': 404
        })

    def test_success_request(self):

        with identity_client.tests.use_cassette('fetch_identity_data/success'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_success_request_with_accounts(self):

        with identity_client.tests.use_cassette('fetch_identity_data/success'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_request_with_expired_accounts(self):

        with identity_client.tests.use_cassette('fetch_identity_data/success_with_expired_accounts'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid, include_expired_accounts=True)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }, {
                u'expiration': u'2010-05-01 00:00:00',
                u'external_id': None,
                u'name': u'Back to the future',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'uuid': u'4b4fcd00-ccb3-4e7b-a1ff-414337963ab1'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Grupo de testes',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'uuid': u'678abf63-eb1e-433d-9f0d-f46b44ab741d'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Test Acount',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'uuid': u'7002ca9a-1d15-4005-b4e3-81adada2bc68'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_request_with_accounts_from_other_services(self):

        with identity_client.tests.use_cassette('fetch_identity_data/success_with_accounts_from_other_services'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid, include_other_services=True)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'name': u'Minhas aplica\xe7\xf5es',
                u'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_request_with_expired_accounts_from_other_services(self):

        with identity_client.tests.use_cassette('fetch_identity_data/success_with_expired_accounts_from_other_services'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid, include_other_services=1, include_expired_accounts=1)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'name': u'Minhas aplica\xe7\xf5es',
                u'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }, {
                u'expiration': u'2010-05-01 00:00:00',
                u'external_id': None,
                u'name': u'Back to the future',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'uuid': u'4b4fcd00-ccb3-4e7b-a1ff-414337963ab1'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Grupo de testes',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'uuid': u'678abf63-eb1e-433d-9f0d-f46b44ab741d'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Test Acount',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'uuid': u'7002ca9a-1d15-4005-b4e3-81adada2bc68'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)


class FetchIdentityDataWithEmail(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_identity_data(email=test_user_email)
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/wrong_credentials'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}',
            'status': 401
        })

    def test_request_with_application_without_permissions(self):

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/application_without_permissions'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': 403, 'message': '403 Client Error: FORBIDDEN'})

    def test_request_with_email_which_does_not_exist(self):

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/email_which_does_not_exist'):
            response = APIClient.fetch_identity_data(email='nao_registrado@email.test')
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'message': u'"Identity with email=nao_registrado@email.test does not exist"',
            'status': 404
        })

    def test_success_request(self):
        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_success_request_with_accounts(self):

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_request_with_expired_accounts(self):

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success_with_expired_accounts'):
            response = APIClient.fetch_identity_data(email=test_user_email, include_expired_accounts=True)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }, {
                u'expiration': u'2010-05-01 00:00:00',
                u'external_id': None,
                u'name': u'Back to the future',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'uuid': u'4b4fcd00-ccb3-4e7b-a1ff-414337963ab1'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Grupo de testes',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'uuid': u'678abf63-eb1e-433d-9f0d-f46b44ab741d'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Test Acount',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'uuid': u'7002ca9a-1d15-4005-b4e3-81adada2bc68'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_request_with_accounts_from_other_services(self):

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success_with_accounts_from_other_services'):
            response = APIClient.fetch_identity_data(email=test_user_email, include_other_services=True)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'name': u'Minhas aplica\xe7\xf5es',
                u'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)

    def test_request_with_expired_accounts_from_other_services(self):

        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success_with_expired_accounts_from_other_services'):
            response = APIClient.fetch_identity_data(email=test_user_email, include_other_services=1, include_expired_accounts=1)
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [{
                u'name': u'Minhas aplica\xe7\xf5es',
                u'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }, {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/',
                u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Ecommerce account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'plan_slug': u'customer',
                u'roles': [u'user'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/',
                u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'My Other Applications',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'plan_slug': u'unittest',
                u'roles': [u'admin'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'No account with this name exists',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/d4ad006d-f61d-4adf-b6e6-849dd15fb419/',
                u'uuid': u'd4ad006d-f61d-4adf-b6e6-849dd15fb419'
            },
            {
                u'expiration': None,
                u'external_id': None,
                u'name': u'Test Account',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'plan_slug': u'unittest-updated',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            }, {
                u'expiration': u'2010-05-01 00:00:00',
                u'external_id': None,
                u'name': u'Back to the future',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/4b4fcd00-ccb3-4e7b-a1ff-414337963ab1/',
                u'uuid': u'4b4fcd00-ccb3-4e7b-a1ff-414337963ab1'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Grupo de testes',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/',
                u'uuid': u'678abf63-eb1e-433d-9f0d-f46b44ab741d'
            }, {
                u'expiration': u'2013-03-01 00:00:00',
                u'external_id': None,
                u'name': u'Test Acount',
                u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/',
                u'uuid': u'7002ca9a-1d15-4005-b4e3-81adada2bc68'
            }],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': True,
            u'last_name': u'Client',
            u'notifications': {
                u'count': 19,
                u'list': u'http://sandbox.app.passaporteweb.com.br/notifications/api/'
            },
            u'profile_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {
                u'identity_client': u'http://sandbox.app.passaporteweb.com.br/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'
            },
            u'update_info_url': u'http://sandbox.app.passaporteweb.com.br/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57'
        })
        self.assertEquals(error, None)


class UpdateUserApi(TestCase):
    """ Estes testes utilizam o usuário criado em InvokeRegistrationApi.  """

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        assert status_code == 200
        self.user_data = content

        self.updated_user_data = {
            'first_name': 'Identity',
            'last_name': 'Client',
            'send_myfreecomm_news': True,
            'send_partner_news': True,
        }

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        form = IdentityInformationForm(self.updated_user_data)
        user_url = self.user_data['update_info_url']
        user_url = user_url.replace('sandbox.app.passaporteweb.com.br', '127.0.0.1:23')

        with identity_client.tests.use_cassette('update_user_api/wrong_api_host'):
            response = APIClient.update_user_api(form, user_url)
            status_code, content, new_form = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.']
        })

    def test_request_with_wrong_credentials(self):
        form = IdentityInformationForm(self.updated_user_data)
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('update_user_api/wrong_credentials'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.']
        })

    def test_request_with_application_without_permissions(self):
        form = IdentityInformationForm(self.updated_user_data)

        with identity_client.tests.use_cassette('update_user_api/application_without_permissions'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            '__all__': [u'Erro no servidor. Entre em contato com o suporte.']
        })

    def test_cpf_already_registered(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = '11111111111'
        self.assertTrue(form.is_valid())

        with identity_client.tests.use_cassette('update_user_api/cpf_already_registered'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Esse número de CPF já está cadastrado.']
        })

    def test_invalid_cpf_pt1(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = '1111111111122222222'

        # This form will not validate, create cleaned_data
        form.cleaned_data = form.data

        with identity_client.tests.use_cassette('update_user_api/invalid_cpf_pt1'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 19).']
        })

    def test_invalid_cpf_pt2(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = 'asdfgqwertzxcvb'

        # This form will not validate, create cleaned_data
        form.cleaned_data = form.data

        with identity_client.tests.use_cassette('update_user_api/invalid_cpf_pt2'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 400)
        self.assertEquals(content, None)
        self.assertEquals(form.errors, {
            u'cpf': [u'Certifique-se de que o valor tenha no máximo 14 caracteres (ele possui 15).']
        })

    def test_success_request(self):
        form = IdentityInformationForm(self.updated_user_data)
        self.assertTrue(form.is_valid())

        with identity_client.tests.use_cassette('update_user_api/success'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': False,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57',
        })
        self.assertEquals(form.errors, {})

    def test_success_request_with_cpf(self):
        form = IdentityInformationForm(self.updated_user_data)
        form.data['cpf'] = '99999999999'
        self.assertTrue(form.is_valid())

        with identity_client.tests.use_cassette('update_user_api/success_with_cpf'):
            response = APIClient.update_user_api(form, self.user_data['update_info_url'])
            status_code, content, new_form = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'accounts': [],
            u'email': u'identity_client@disposableinbox.com',
            u'first_name': u'Identity',
            u'is_active': False,
            u'last_name': u'Client',
            u'notifications': {u'count': 0, u'list': u'/notifications/api/'},
            u'profile_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/profile/',
            u'send_myfreecomm_news': True,
            u'send_partner_news': True,
            u'services': {u'identity_client': u'/accounts/api/service-info/c3769912-baa9-4a0c-9856-395a706c7d57/identity_client/'},
            u'update_info_url': u'/accounts/api/identities/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'uuid': u'c3769912-baa9-4a0c-9856-395a706c7d57',
            u'cpf': u'99999999999',
        })
        self.assertEquals(form.errors, {})


class FetchAssociationData(TestCase):

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        assert status_code == 200
        self.user_data = content

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        association_url = self.user_data['services']['identity_client']
        association_url = association_url.replace('sandbox.app.passaporteweb.com.br', '127.0.0.1:23')
        response = APIClient.fetch_association_data(association_url)
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with identity_client.tests.use_cassette('fetch_association_data/wrong_credentials'):
            response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
            status_code, content, error = response

        APIClient.pweb.auth = (settings.PASSAPORTE_WEB['CONSUMER_TOKEN'], settings.PASSAPORTE_WEB['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'ecommerce')

        with identity_client.tests.use_cassette('fetch_association_data/application_without_permissions'):
            response = APIClient.fetch_association_data(association_url)
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_for_association_which_does_not_exist(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'gFXrVmzDXXZm')

        with identity_client.tests.use_cassette('fetch_association_data/association_which_does_not_exist'):
            response = APIClient.fetch_association_data(association_url)
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_success_without_data(self):
        with identity_client.tests.use_cassette('fetch_association_data/success_without_data'):
            response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {u'is_active': True, u'slug': u'identity_client'})
        self.assertEquals(error, None)

    def test_success_with_data(self):
        with identity_client.tests.use_cassette('fetch_association_data/success_with_data'):
            response = APIClient.fetch_association_data(self.user_data['services']['identity_client'])
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'timezone': u'America/Sao_Paulo',
            u'is_active': True,
            u'updated_at': u'2013-06-24 14:55:00',
            u'updated_by': u'identity_client.UpdateAssociationData',
            u'slug': u'identity_client'
        })
        self.assertEquals(error, None)


class UpdateAssociationData(TestCase):

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_identity_data_with_email/success'):
            response = APIClient.fetch_identity_data(email=test_user_email)
            status_code, content, error = response

        assert status_code == 200
        self.user_data = content

        self.association_data = {
            'updated_by': 'identity_client.UpdateAssociationData',
            'updated_at': '2013-06-24 14:55:00',
            'timezone': 'America/Sao_Paulo',
        }

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        association_url = self.user_data['services']['identity_client']
        association_url = association_url.replace('sandbox.app.passaporteweb.com.br', '127.0.0.1:23')
        response = APIClient.update_association_data(self.association_data, association_url)
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.pweb.auth = ('?????', 'XXXXXX')

        with identity_client.tests.use_cassette('update_association_data/wrong_credentials'):
            response = APIClient.update_association_data(self.association_data, self.user_data['services']['identity_client'])
            status_code, content, error = response

        APIClient.pweb.auth = (settings.PASSAPORTE_WEB['CONSUMER_TOKEN'], settings.PASSAPORTE_WEB['CONSUMER_SECRET'])

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'ecommerce')

        with identity_client.tests.use_cassette('update_association_data/application_without_permissions'):
            response = APIClient.update_association_data(self.association_data, association_url)
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_for_association_which_does_not_exist(self):
        association_url =  self.user_data['services']['identity_client']
        association_url = association_url.replace('identity_client', 'gFXrVmzDXXZm')

        with identity_client.tests.use_cassette('update_association_data/association_which_does_not_exist'):
            response = APIClient.update_association_data(self.association_data, association_url)
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_success_with_data(self):
        with identity_client.tests.use_cassette('update_association_data/success_with_data'):
            response = APIClient.update_association_data(self.association_data, self.user_data['services']['identity_client'])
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'timezone': u'America/Sao_Paulo',
            u'is_active': True,
            u'updated_at': u'2013-06-24 14:55:00',
            u'updated_by': u'identity_client.UpdateAssociationData',
            u'slug': u'identity_client'
        })
        self.assertEquals(error, None)

    def test_success_without_data(self):
        with identity_client.tests.use_cassette('update_association_data/success_without_data'):
            response = APIClient.update_association_data({}, self.user_data['services']['identity_client'])
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {u'is_active': True, u'slug': u'identity_client'})
        self.assertEquals(error, None)

    def test_success_with_xml_payload(self):
        data_with_xml = self.association_data.copy()
        data_with_xml['payload'] = {
            'content-type': 'application/xml',
            'body': u'<?xml version="1.0" encoding="UTF-8" ?> <俄语>данные</俄语>'
        }

        with identity_client.tests.use_cassette('update_association_data/success_with_xml_payload'):
            response = APIClient.update_association_data(data_with_xml, self.user_data['services']['identity_client'])
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'timezone': u'America/Sao_Paulo',
            u'is_active': True,
            u'updated_at': u'2013-06-24 14:55:00',
            u'updated_by': u'identity_client.UpdateAssociationData',
            u'slug': u'identity_client',
            u'payload': {
                u'content-type': u'application/xml',
                u'body': u'<?xml version="1.0" encoding="UTF-8" ?> <俄语>данные</俄语>'
            }
        })
        self.assertEquals(error, None)


class FetchUserAccounts(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_user_accounts(uuid=test_user_uuid)
        status_code, accounts, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('fetch_user_accounts/wrong_credentials'):
            response = APIClient.fetch_user_accounts(uuid=test_user_uuid)
            status_code, accounts, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/application_without_permissions'):
            response = APIClient.fetch_user_accounts(uuid=test_user_uuid)
            status_code, accounts, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/uuid_which_does_not_exist'):
            response = APIClient.fetch_user_accounts(uuid='00000000-0000-0000-0000-000000000000')
            status_code, accounts, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_success_without_accounts(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_without_accounts'):
            response = APIClient.fetch_user_accounts(test_user_uuid)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [])
        self.assertEquals(error, None)

    def test_success_with_accounts(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_accounts'):
            response = APIClient.fetch_user_accounts(test_user_uuid)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [{
            u'account_data': {u'name': u'Test Account', u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'},
            u'add_member_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
            u'expiration': None,
            u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest',
            u'roles': [u'owner'],
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
        }])
        self.assertEquals(error, None)

    def test_success_with_expired_accounts(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_expired_accounts'):
            response = APIClient.fetch_user_accounts(test_user_uuid, include_expired_accounts=True)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [{
            u'account_data': {u'name': u'My Other Applications',
            u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
            u'add_member_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/',
            u'expiration': None,
            u'membership_details_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest',
            u'roles': [u'owner'],
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/'
        }, {
            u'account_data': {u'name': u'Test Account',
            u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'},
            u'add_member_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
            u'expiration': u'0001-01-01',
            u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest-updated',
            u'roles': [u'owner'],
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/'
        }])
        self.assertEquals(error, None)

    def test_success_with_expired_accounts_from_other_services(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_expired_accounts_from_other_services'):
            response = APIClient.fetch_user_accounts(test_user_uuid, include_other_services=1, include_expired_accounts=1)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [
            {
                u'account_data': {u'name': u'Test Acount', u'uuid': u'7002ca9a-1d15-4005-b4e3-81adada2bc68'},
                u'add_member_url': u'/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/members/',
                u'expiration': u'2013-03-01',
                u'membership_details_url': u'/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/7002ca9a-1d15-4005-b4e3-81adada2bc68/'
            }, {
                u'account_data': {u'name': u'Ecommerce account', u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'},
                u'add_member_url': u'/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/'
            }, {
                u'account_data': {u'name': u'My Other Applications', u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
                u'add_member_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/'
            }, {
                u'account_data': {u'name': u'Test Account', u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'},
                u'add_member_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/'
            }, {
                u'account_data': {u'name': u'Ecommerce Account', u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'},
                u'add_member_url': u'/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/members/',  u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/'
            }, {
                u'account_data': {u'name': u' ', u'uuid': u'678abf63-eb1e-433d-9f0d-f46b44ab741d'},
                u'add_member_url': u'/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/members/',
                u'expiration': u'2013-03-01',
                u'membership_details_url': u'/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/678abf63-eb1e-433d-9f0d-f46b44ab741d/'
            }, {
                u'name': u'Minhas aplicações', u'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }
        ])
        self.assertEquals(error, None)

    def test_success_with_accounts_from_other_services(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_accounts_from_other_services'):
            response = APIClient.fetch_user_accounts(test_user_uuid, include_other_services=True)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [
            {
                u'account_data': {u'name': u'Ecommerce account', u'uuid': u'48aeff34-20c9-4039-bd97-d815020e8b44'},
                u'add_member_url': u'/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'customer',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/48aeff34-20c9-4039-bd97-d815020e8b44/'
            }, {
                u'account_data': {u'name': u'My Other Applications', u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
                u'add_member_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/'
            }, {
                u'account_data': {u'name': u'Test Account', u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'},
                u'add_member_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/'
            }, {
                u'account_data': {u'name': u'Ecommerce Account', u'uuid': u'5f15f7b5-a7f6-4a35-8573-0da53d303e18'},
                u'add_member_url': u'/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/members/',  u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'seller',
                u'roles': [u'owner'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/5f15f7b5-a7f6-4a35-8573-0da53d303e18/'
            },
            {
                u'name': u'Minhas aplicações', u'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }
        ])
        self.assertEquals(error, None)

    def test_success_with_only_accounts_with_a_given_role(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_only_accounts_with_a_given_role'):
            response = APIClient.fetch_user_accounts(test_user_uuid, role='admin')
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [{
            u'account_data': {u'name': u'My Other Applications',
            u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
            u'add_member_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/',
            u'expiration': None,
            u'membership_details_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest',
            u'roles': [u'owner', u'admin'],
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/'
        }])
        self.assertEquals(error, None)

    def test_success_with_only_accounts_with_a_given_role_in_all_services(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_only_accounts_with_a_given_role_in_all_services'):
            response = APIClient.fetch_user_accounts(test_user_uuid, role='admin', include_other_services=1)
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [
            {
                u'account_data': {u'name': u'My Other Applications',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
                u'add_member_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner', u'admin'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/'
            }, {
                u'name': u'Minhas aplicações', 'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }
        ])
        self.assertEquals(error, None)

    def test_success_with_only_accounts_with_a_given_role_in_all_services_including_expired(self):
        with identity_client.tests.use_cassette('fetch_user_accounts/success_with_only_accounts_with_a_given_role_in_all_services_including_expired'):
            response = APIClient.fetch_user_accounts(test_user_uuid,
                role='admin', include_other_services=1, include_expired_accounts=1
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(accounts, [
            {
                u'account_data': {u'name': u'My Other Applications',
                u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
                u'add_member_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/',
                u'expiration': None,
                u'membership_details_url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'plan_slug': u'unittest',
                u'roles': [u'owner', u'admin'],
                u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
                u'url': u'/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/'
            }, {
                u'name': u'Minhas aplicações', 'uuid': u'1bcde52d-7da8-4800-bd59-dfea96933ce4'
            }
        ])
        self.assertEquals(error, None)


class FetchAccountData(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
        status_code, account, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(account, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('fetch_account_data/wrong_credentials'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            status_code, account, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('fetch_account_data/application_without_permissions'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            status_code, account, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('fetch_account_data/uuid_which_does_not_exist'):
            response = APIClient.fetch_account_data(account_uuid='00000000-0000-0000-0000-000000000000')
            status_code, account, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Account 00000000-0000-0000-0000-000000000000 has no relation with service identity_client"'
        })

    def test_success(self):
        with identity_client.tests.use_cassette('fetch_account_data/success'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            status_code, account, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(account, {
            u'account_data': {
                    u'name': u'Test Account', u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            },
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
            u'expiration': None,
            u'history_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/history/',
            u'members_data': [{
                u'identity': u'c3769912-baa9-4a0c-9856-395a706c7d57',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'roles': [u'owner']
            }, {
                u'identity': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
                u'roles': [u'user']
            }, {
                u'identity': u'1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d/',
                u'roles': [u'owner']
            }],
            u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'plan_slug': u'unittest-updated',
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'updated_at': u'2014-01-09 20:18:28',
            u'updated_by': u'http://sandbox.app.passaporteweb.com.br/admin/applications/identity_client/',
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/'
        })

        self.assertEquals(error, None)

    def test_reading_expired_accounts_fails(self):
        with identity_client.tests.use_cassette('fetch_account_data/expired_accounts'):
            response = APIClient.fetch_account_data(test_user_uuid)
            status_code, account, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Account c3769912-baa9-4a0c-9856-395a706c7d57 has no relation with service identity_client"'
        })


class CreateUserAccount(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.create_user_account(uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest')
        status_code, accounts, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('create_user_account/wrong_credentials'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest')
            status_code, accounts, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('create_user_account/application_without_permissions'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest')
            status_code, accounts, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('create_user_account/uuid_which_does_not_exist'):
            response = APIClient.create_user_account(
                uuid='00000000-0000-0000-0000-000000000000', account_name='Test Account', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_request_with_empty_name(self):
        # Este teste não faz mais requisição para a api, porem se fizer esta será a resposta
        with identity_client.tests.use_cassette('create_user_account/with_empty_name'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_name='', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': None,
            'message': u"Unexpected error: Either 'account_uuid' or 'account_name' must be given <<type 'exceptions.ValueError'>>",
        })

    def test_request_with_invalid_expiration(self):
        with identity_client.tests.use_cassette('create_user_account/with_invalid_expiration'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest', expiration='ABC'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"expiration": ["Informe uma data v\\u00e1lida."]}}'
        })

    def test_request_with_expiration_in_the_past(self):
        with identity_client.tests.use_cassette('create_user_account/with_expiration_in_the_past'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest', expiration='0000-01-01'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"expiration": ["Informe uma data v\\u00e1lida."]}}'
        })

    def test_request_with_expiration_after_max_date(self):
        with identity_client.tests.use_cassette('create_user_account/with_expiration_after_max_date'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest', expiration='10000-01-01'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"expiration": ["Informe uma data v\\u00e1lida."]}}'
        })

    def test_success_request(self):
        with identity_client.tests.use_cassette('create_user_account/success'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 201)
        self.assertEquals(accounts, {
            u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest',
            u'roles': [u'owner'],
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'expiration': None,
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'account_data': {u'name': u'Test Account', u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'},
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/'
        })
        self.assertEquals(error, None)

    def test_duplicated_account(self):
        with identity_client.tests.use_cassette('create_user_account/duplicated_account'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_name='Test Account', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 409)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 409,
            'message': u'"ServiceAccount for service identity_client and account \'Test Account\' already exists and is active. Conflict"'
        })


class CreateUserAccountWithUUID(TestCase):

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest')
        status_code, accounts, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('create_user_account_with_uuid/wrong_credentials'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest')
            status_code, accounts, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/application_without_permissions'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest')
            status_code, accounts, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_user_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/uuid_which_does_not_exist'):
            response = APIClient.create_user_account(
                uuid='00000000-0000-0000-0000-000000000000', account_name='Test Account', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_request_with_account_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/account_uuid_which_does_not_exist'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_uuid='00000000-0000-0000-0000-000000000000', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"uuid": ["This UUID does not match any account."]}, "errors": ["Either name or uuid must be supplied."]}'
        })

    def test_request_with_empty_account_uuid(self):
        # Este teste não faz mais requisição para a api, porem se fizer esta será a resposta
        with identity_client.tests.use_cassette('create_user_account_with_uuid/with_empty_name'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid, account_uuid='', plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': None,
            'message': u"Unexpected error: Either 'account_uuid' or 'account_name' must be given <<type 'exceptions.ValueError'>>",
        })

    def test_request_with_invalid_expiration(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/with_invalid_expiration'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest', expiration='ABC')
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"expiration": ["Informe uma data v\\u00e1lida."]}}'
        })

    def test_request_with_expiration_in_the_past(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/with_expiration_in_the_past'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest', expiration='0000-01-01')
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"expiration": ["Informe uma data v\\u00e1lida."]}}'
        })

    def test_request_with_expiration_after_max_date(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/with_expiration_after_max_date'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest', expiration='10000-01-01')
            status_code, accounts, error = response

        self.assertEquals(status_code, 400)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 400,
            'message': u'{"field_errors": {"expiration": ["Informe uma data v\\u00e1lida."]}}'
        })

    def test_success_request(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/success'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid,
                account_uuid=second_account_uuid,
                plan_slug='unittest'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 201)
        self.assertEquals(accounts, {
            u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest',
            u'roles': [u'owner'],
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/',
            u'expiration': None,
            u'service_data': {u'name': u'Identity Client',
            u'slug': u'identity_client'},
            u'account_data': {u'name': u'My Other Applications',
            u'uuid': u'e5ab6f2f-a4eb-431b-8c12-9411fd8a872d'},
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/members/'
        })
        self.assertEquals(error, None)

    def test_duplicated_account(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/duplicated_account'):
            response = APIClient.create_user_account(uuid=test_user_uuid, account_uuid=test_account_uuid, plan_slug='unittest')
            status_code, accounts, error = response

        self.assertEquals(status_code, 409)
        self.assertEquals(accounts, None)
        self.assertEquals(error, {
            'status': 409,
            'message': u'"ServiceAccount for service identity_client and account \'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba\' already exists and is active. Conflict"'
        })

    def test_creating_user_account_with_uuid_of_expired_account(self):
        with identity_client.tests.use_cassette('create_user_account_with_uuid/with_uuid_of_expired_account'):
            response = APIClient.create_user_account(
                uuid=test_user_uuid,
                account_uuid=test_account_uuid,
                plan_slug='unittest-expired'
            )
            status_code, accounts, error = response

        self.assertEquals(status_code, 201)
        self.assertEquals(accounts, {
            u'account_data': {u'name': u'Test Account', u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'},
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
            u'expiration': None,
        u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
            u'plan_slug': u'unittest-expired',
            u'roles': [u'owner'],
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/'
        })
        self.assertEquals(error, None)


class UpdateAccountData(TestCase):

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_account_data/success'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            status_code, account, error = response

        self.account_data = account
        self.new_plan = 'unittest-updated'
        self.new_expiration = date.max

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        api_path = self.account_data['url']
        api_path = api_path.replace('sandbox.app.passaporteweb.com.br', '127.0.0.1:23')

        response = APIClient.update_account_data(plan_slug=self.new_plan, expiration=self.new_expiration, api_path=api_path)
        status_code, account, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(account, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('update_account_data/wrong_credentials'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=self.new_expiration, api_path=self.account_data['url']
            )
            status_code, account, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('update_account_data/application_without_permissions'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=self.new_expiration, api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('update_account_data/uuid_which_does_not_exist'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=self.new_expiration,
                api_path=self.account_data['url'].replace(test_account_uuid, '00000000-0000-0000-0000-000000000000')
            )
            status_code, account, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Account 00000000-0000-0000-0000-000000000000 has no relation with service identity_client"'
        })

    def test_expiration_cannot_be_a_string(self):
        with identity_client.tests.use_cassette('update_account_data/expiration_cannot_be_a_string'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration='9999-12-31', api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': None,
            'message': u"Unexpected error: expiration must be a date instance or None <<type 'exceptions.TypeError'>>"}
        )

    def test_expiration_cannot_be_a_datetime(self):
        with identity_client.tests.use_cassette('update_account_data/expiration_cannot_be_a_datetime'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=datetime.max, api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': None,
            'message': u"Unexpected error: expiration must be a date instance or None <<type 'exceptions.TypeError'>>"}
        )

    def test_expiration_cannot_be_a_float(self):
        with identity_client.tests.use_cassette('update_account_data/expiration_cannot_be_a_float'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=time.time(), api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': None,
            'message': u"Unexpected error: expiration must be a date instance or None <<type 'exceptions.TypeError'>>"}
        )

    def test_expiration_cannot_be_an_int(self):
        with identity_client.tests.use_cassette('update_account_data/expiration_cannot_be_an_int'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=int(time.time()), api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(account, None)
        self.assertEquals(error, {
            'status': None,
            'message': u"Unexpected error: expiration must be a date instance or None <<type 'exceptions.TypeError'>>"}
        )

    def test_expiration_can_be_None(self):
        with identity_client.tests.use_cassette('update_account_data/expiration_can_be_none'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=None, api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(account, {
            u'account_data': {
                u'name': u'Test Account',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            },
            u'members_data': [{
                u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'roles': [u'owner'],
                u'identity': u'c3769912-baa9-4a0c-9856-395a706c7d57'
            }],
            u'url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'expiration': None,
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'plan_slug': u'unittest-updated',
            u'add_member_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
        })
        self.assertEquals(error, None)

    def test_expiration_can_be_set_to_the_past(self):
        with identity_client.tests.use_cassette('update_account_data/expiration_can_be_set_to_the_past'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=date(1900, 1, 1), api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(account, {
            u'account_data': {
                u'name': u'Test Account',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            },
            u'members_data': [{
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'roles': [u'owner'],
                u'identity': u'c3769912-baa9-4a0c-9856-395a706c7d57'
            }, {
                u'identity': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
                u'roles': [u'user']
            }, {
                u'identity': u'1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d/',
                u'roles': [u'owner']
            }],
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'updated_at': u'2014-01-10 20:25:25',
            u'updated_by': u'http://sandbox.app.passaporteweb.com.br/admin/applications/identity_client/',
            u'history_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/history/',
            u'expiration': '1900-01-01 00:00:00',
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'plan_slug': u'unittest-updated',
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
        })
        self.assertEquals(error, None)

    def test_success(self):
        with identity_client.tests.use_cassette('update_account_data/success'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=self.new_expiration, api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(account, {
            u'account_data': {
                u'name': u'Test Account',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            },
            u'members_data': [{
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'roles': [u'owner'],
                u'identity': u'c3769912-baa9-4a0c-9856-395a706c7d57'
            }, {
                u'identity': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
                u'roles': [u'user']
            }, {
                u'identity': u'1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d/',
                u'roles': [u'owner']
            }],
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'updated_at': u'2014-01-10 20:46:24',
            u'updated_by': u'http://sandbox.app.passaporteweb.com.br/admin/applications/identity_client/',
            u'history_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/history/',
            u'expiration': '9999-12-31 00:00:00',
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'plan_slug': u'unittest-updated',
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
        })
        self.assertEquals(error, None)

    def test_expired_accounts_can_have_plan_changed(self):
        with identity_client.tests.use_cassette('update_account_data/expired_accounts_can_have_plan_changed'):
            response = APIClient.update_account_data(
                plan_slug='expired-service', expiration=date(1900, 1, 1), api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(account, {
            u'account_data': {
                u'name': u'Test Account',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            },
            u'members_data': [{
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'roles': [u'owner'],
                u'identity': u'c3769912-baa9-4a0c-9856-395a706c7d57'
            }, {
                u'identity': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
                u'roles': [u'user']
            }, {
                u'identity': u'1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d/',
                u'roles': [u'owner']
            }],
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'updated_at': u'2014-01-10 20:40:14',
            u'updated_by': u'http://sandbox.app.passaporteweb.com.br/admin/applications/identity_client/',
            u'history_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/history/',
            u'expiration': '1900-01-01 00:00:00',
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'plan_slug': u'expired-service',
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
        })
        self.assertEquals(error, None)

    def test_expired_accounts_can_have_expiration_changed(self):
        with identity_client.tests.use_cassette('update_account_data/expired_accounts_can_have_expiration_changed'):
            response = APIClient.update_account_data(
                plan_slug=self.new_plan, expiration=date(1903, 1, 1), api_path=self.account_data['url']
            )
            status_code, account, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(account, {
            u'account_data': {
                u'name': u'Test Account',
                u'uuid': u'a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba'
            },
            u'members_data': [{
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/c3769912-baa9-4a0c-9856-395a706c7d57/',
                u'roles': [u'owner'],
                u'identity': u'c3769912-baa9-4a0c-9856-395a706c7d57'
            }, {
                u'identity': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
                u'roles': [u'user']
            }, {
                u'identity': u'1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d',
                u'membership_details_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/1cf30b5f-e78c-4eb9-a7b2-294a1d024e6d/',
                u'roles': [u'owner']
            }],
            u'url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'notifications_url': u'http://sandbox.app.passaporteweb.com.br/notifications/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/',
            u'updated_at': u'2014-01-10 20:49:03',
            u'updated_by': u'http://sandbox.app.passaporteweb.com.br/admin/applications/identity_client/',
            u'history_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/history/',
            u'expiration': '1903-01-01 00:00:00',
            u'service_data': {u'name': u'Identity Client', u'slug': u'identity_client'},
            u'plan_slug': u'unittest-updated',
            u'add_member_url': u'http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/',
        })
        self.assertEquals(error, None)


class AddAccountMember(TestCase):

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_account_data/success'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            _, account, _ = response

        self.account_data = account

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        api_path = self.account_data['add_member_url']
        api_path = api_path.replace('sandbox.app.passaporteweb.com.br', '127.0.0.1:23')

        response = APIClient.add_account_member(
            user_uuid=test_user_uuid, roles=['user'], api_path=api_path
        )
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('add_account_member/wrong_credentials'):
            response = APIClient.add_account_member(
                user_uuid=test_user_uuid, roles=['user'], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('add_account_member/application_without_permissions'):
            response = APIClient.add_account_member(
                user_uuid=test_user_uuid, roles=['user'], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('add_account_member/uuid_which_does_not_exist'):
            response = APIClient.add_account_member(
                user_uuid='00000000-0000-0000-0000-000000000000', roles=['user'], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_request_with_user_which_is_already_a_member(self):
        with identity_client.tests.use_cassette('add_account_member/already_a_member'):
            response = APIClient.add_account_member(
                user_uuid=test_user_uuid, roles=['user'], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 409)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 409,
            'message': u'"Identity with uuid=c3769912-baa9-4a0c-9856-395a706c7d57 is already in members list of service identity_client at account a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba"'
        })

    def test_request_with_empty_roles_list_gives_user_role(self):
        with identity_client.tests.use_cassette('add_account_member/empty_roles_list'):
            response = APIClient.add_account_member(
                user_uuid=second_user_uuid, roles=[], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'user']
        })
        self.assertEquals(error, None)

    def test_success_with_user_role(self):
        with identity_client.tests.use_cassette('add_account_member/success_with_user_role'):
            response = APIClient.add_account_member(
                user_uuid=second_user_uuid, roles=['user'], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'user']
        })
        self.assertEquals(error, None)

    def test_success_with_owner_role(self):
        with identity_client.tests.use_cassette('add_account_member/success_with_owner_role'):
            response = APIClient.add_account_member(
                user_uuid=second_user_uuid, roles=['owner'], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'owner']
        })
        self.assertEquals(error, None)

    def test_success_with_list_of_roles(self):
        with identity_client.tests.use_cassette('add_account_member/success_with_list_of_roles'):
            response = APIClient.add_account_member(
                user_uuid=second_user_uuid,
                roles=['owner', 'user', range(5), 12345, 01234, {'a': 'A'}, 'test-user', u'çãéê®©þ«»'],
                api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'membership_details_url': u'/organizations/api/accounts/a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba/members/bedcd531-c741-4d32-90d7-a7f7432f3f15/',
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'[0, 1, 2, 3, 4]', u'çãéê®©þ«»', u'test-user', u'668', u'user', u"{'a': 'a'}", u'owner', u'12345']
        })
        self.assertEquals(error, None)

    def test_adding_members_to_an_expired_account_fails(self):
        with identity_client.tests.use_cassette('add_account_member/expired_account'):
            response = APIClient.add_account_member(
                user_uuid=test_user_uuid, roles=[], api_path=self.account_data['add_member_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Account a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba and service identity_client are not related"'
        })


class UpdateMemberRoles(TestCase):

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_account_data/success'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            _, account_data, _ = response

            with identity_client.tests.use_cassette('add_account_member/success_with_user_role'):
                response = APIClient.add_account_member(
                    user_uuid=second_user_uuid, roles=['user'], api_path=account_data['add_member_url']
                )
                _, content, _ = response

        self.member_data = content

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.update_member_roles(
            roles=['user'], api_path=self.member_data['membership_details_url']
        )
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('update_member_roles/wrong_credentials'):
            response = APIClient.update_member_roles(
                roles=['user'], api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('update_member_roles/application_without_permissions'):
            response = APIClient.update_member_roles(
                roles=['user'], api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_request_with_empty_roles_list_gives_user_role(self):
        with identity_client.tests.use_cassette('update_member_roles/empty_roles_list'):
            response = APIClient.update_member_roles(
                roles=[], api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'user']
        })
        self.assertEquals(error, None)

    def test_success_with_user_role(self):
        with identity_client.tests.use_cassette('update_member_roles/success_with_user_role'):
            response = APIClient.update_member_roles(
                roles=['user'], api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'user']
        })
        self.assertEquals(error, None)

    def test_success_with_owner_role(self):
        with identity_client.tests.use_cassette('update_member_roles/success_with_owner_role'):
            response = APIClient.update_member_roles(
                roles=['owner'], api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'owner']
        })
        self.assertEquals(error, None)

    def test_success_with_list_of_roles(self):
        with identity_client.tests.use_cassette('update_member_roles/success_with_list_of_roles'):
            response = APIClient.update_member_roles(
                roles=['owner', 'user', range(5), 12345, 01234, {'a': 'A'}, 'test-user', u'çãéê®©þ«»'],
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 200)
        self.assertEquals(content, {
            u'identity': {
                u'first_name': u'Identity',
                u'last_name': u'Client',
                u'send_partner_news': True,
                u'uuid': u'bedcd531-c741-4d32-90d7-a7f7432f3f15',
                u'is_active': True,
                u'send_myfreecomm_news': True,
                u'email': u'identity_client_2@disposableinbox.com'
            },
            u'roles': [u'[0, 1, 2, 3, 4]', u'çãéê®©þ«»', u'test-user', u'668', u'user', u"{'a': 'a'}", u'owner', u'12345']
        })
        self.assertEquals(error, None)

    def test_request_with_user_uuid_which_is_not_a_member(self):
        with identity_client.tests.use_cassette('update_member_roles/user_uuid_not_a_member'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity bedcd531-c741-4d32-90d7-a7f7432f3f15 is not member of service identity_client for account a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba"'
        })

    def test_request_with_account_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('update_member_roles/account_uuid_which_does_not_exist'):
            response = APIClient.update_member_roles(
                roles=[],
                api_path=self.member_data['membership_details_url'].replace(test_account_uuid, '00000000-0000-0000-0000-000000000000')
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404, 'message': u'"Account with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_request_with_user_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('update_member_roles/user_uuid_which_does_not_exist'):
            response = APIClient.update_member_roles(
                roles=[],
                api_path=self.member_data['membership_details_url'].replace(second_user_uuid, '00000000-0000-0000-0000-000000000000')
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404, 'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_updating_members_of_an_expired_account_fails(self):
        with identity_client.tests.use_cassette('update_member_roles/expired_account'):
            response = APIClient.update_member_roles(
                roles=['owner'], api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Account a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba and service identity_client are not related"'
        })


class RemoveAccountMember(TestCase):

    def setUp(self):
        with identity_client.tests.use_cassette('fetch_account_data/success'):
            response = APIClient.fetch_account_data(account_uuid=test_account_uuid)
            _, account_data, _ = response

            with identity_client.tests.use_cassette('add_account_member/success_with_user_role'):
                response = APIClient.add_account_member(
                    user_uuid=second_user_uuid, roles=['user'], api_path=account_data['add_member_url']
                )
                _, content, _ = response

        self.member_data = content

    @patch.object(APIClient, 'api_host', 'http://127.0.0.1:23')
    def test_request_with_wrong_api_host(self):
        response = APIClient.remove_account_member(
            api_path=self.member_data['membership_details_url']
        )
        status_code, content, error = response

        self.assertEquals(status_code, 500)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': None, 'message': 'Error connecting to PassaporteWeb'})

    def test_request_with_wrong_credentials(self):
        APIClient.api_user = '?????'
        APIClient.api_password = 'XXXXXX'

        with identity_client.tests.use_cassette('remove_account_member/wrong_credentials'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        APIClient.api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        APIClient.api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']

        self.assertEquals(status_code, 401)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 401,
            'message': u'{"detail": "You need to login or otherwise authenticate the request."}'
        })

    def test_request_with_application_without_permissions(self):
        with identity_client.tests.use_cassette('remove_account_member/application_without_permissions'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 403)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 403,
            'message': u'{"detail": "You do not have permission to access this resource. You may need to login or otherwise authenticate the request."}'
        })

    def test_success(self):
        with identity_client.tests.use_cassette('remove_account_member/success'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 204)
        self.assertEquals(content, '')
        self.assertEquals(error, None)

    def test_removing_user_with_owner_role(self):
        with identity_client.tests.use_cassette('remove_account_member/remove_owner'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 406)
        self.assertEquals(content, None)
        self.assertEquals(error, {'status': 406, 'message': u'"Service owner cannot be removed from members list"'})

    def test_request_with_user_uuid_which_is_not_a_member(self):
        with identity_client.tests.use_cassette('remove_account_member/user_uuid_not_a_member'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity bedcd531-c741-4d32-90d7-a7f7432f3f15 is not member of service identity_client for account a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba"'
        })

    def test_request_with_account_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('remove_account_member/account_uuid_which_does_not_exist'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url'].replace(test_account_uuid, '00000000-0000-0000-0000-000000000000')
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404, 'message': u'"Account with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_request_with_user_uuid_which_does_not_exist(self):
        with identity_client.tests.use_cassette('remove_account_member/user_uuid_which_does_not_exist'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url'].replace(second_user_uuid, '00000000-0000-0000-0000-000000000000')
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404, 'message': u'"Identity with uuid=00000000-0000-0000-0000-000000000000 does not exist"'
        })

    def test_removing_members_of_an_expired_account_fails(self):
        with identity_client.tests.use_cassette('remove_account_member/expired_account'):
            response = APIClient.remove_account_member(
                api_path=self.member_data['membership_details_url']
            )
            status_code, content, error = response

        self.assertEquals(status_code, 404)
        self.assertEquals(content, None)
        self.assertEquals(error, {
            'status': 404,
            'message': u'"Identity bedcd531-c741-4d32-90d7-a7f7432f3f15 is not member of service identity_client for account a4c9bce4-2a8c-452f-ae13-0a0b69dfd4ba"'
        })
