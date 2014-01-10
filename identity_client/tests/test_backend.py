# -*- coding: utf-8 -*-
import json

from mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

import identity_client
from identity_client.models import Identity
from identity_client.backend import MyfcidAPIBackend, get_user
from identity_client.utils import get_account_module
from identity_client.tests.helpers import MyfcIDTestCase as TestCase
from identity_client.client_api_methods import APIClient

__all__ = ['TestMyfcidApiBackend', 'TestGetUser', 'TestFetchUserData']

test_user_email = 'identity_client@disposableinbox.com'
test_user_password = '*SudN7%r$MiYRa!E'
test_user_uuid = 'c3769912-baa9-4a0c-9856-395a706c7d57'


class TestMyfcidApiBackend(TestCase):

    def test_successful_auth(self):
        # Autenticar um usuário
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # Checar se o usuário foi autenticado corretamente
        self.assertNotEqual(identity, None)
        self.assertEquals(identity.first_name, 'Identity')
        self.assertEquals(identity.last_name, 'Client')
        self.assertEquals(identity.email, test_user_email)
        self.assertEquals(identity.user_data, {
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

        # Checar se o backend foi setado corretamente
        self.assertEquals(
            identity.backend,
            '%s.%s' % (MyfcidAPIBackend.__module__, 'MyfcidAPIBackend')
        )


    def test_failed_auth(self):
        # Autenticar um usuário
        with identity_client.tests.use_cassette('myfcid_api_backend/wrong_password'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, 'senha errada')

        # Garantir que o usuario não foi autenticado
        self.assertEquals(identity, None)


    def test_auth_updates_user(self):
        # Create a user
        user = Identity.objects.create(uuid=test_user_uuid, email='vai_mudar@email.com')

        # Autenticar um usuário
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # Checar se os dados do usuário foram atualizados
        self.assertEquals(identity.first_name, 'Identity')
        self.assertEquals(identity.last_name, 'Client') 
        self.assertEquals(identity.email, test_user_email)
        self.assertEquals(identity.uuid, test_user_uuid)


    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_create_local_identity_creates_user_accounts(self):
        # Obter dados do usuário
        with identity_client.tests.use_cassette('fetch_identity_data/success_with_accounts'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        # Criar usuário local
        identity = MyfcidAPIBackend().create_local_identity(content)

        # 1 conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 3)


    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_create_local_identity_removes_user_from_old_accounts(self):
        # Obter dados do usuário
        with identity_client.tests.use_cassette('fetch_identity_data/success'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        # Criar usuário local
        identity = MyfcidAPIBackend().create_local_identity(content)

        # 5 contas devem ter sido criadas
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 5)

        # Obter os dados do usuário, desta vez sem accounts
        with identity_client.tests.use_cassette('fetch_identity_data/success_with_accounts'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        # Criar usuário local
        identity = MyfcidAPIBackend().create_local_identity(content)

        # O usuário deve ter sido dissociado da account
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 3)


    def test_accounts_creation_fails_if_settings_are_wrong(self):
        # Obter dados do usuário
        with identity_client.tests.use_cassette('fetch_identity_data/success_with_accounts'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        # Criar usuário local
        with patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'unknown_app.UnknownModel'):
            identity = MyfcidAPIBackend().create_local_identity(content)

        self.assertTrue(identity is not None)

        # Nenhuma conta foi criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)


    def test_auth_user_accounts_creation_fails_if_settings_are_missing(self):
        # Obter dados do usuário
        with identity_client.tests.use_cassette('fetch_identity_data/success_with_accounts'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        # Criar usuário local
        with patch.object(settings, 'SERVICE_ACCOUNT_MODULE', None):
            identity = MyfcidAPIBackend().create_local_identity(content)

        self.assertTrue(identity is not None)

        # Nenhuma conta foi criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 0)


    @patch.object(settings, 'SERVICE_ACCOUNT_MODULE', 'identity_client.ServiceAccount')
    def test_authentication_should_not_remove_user_accounts(self):
        # Obter dados do usuário
        with identity_client.tests.use_cassette('fetch_identity_data/success_with_accounts'):
            response = APIClient.fetch_identity_data(uuid=test_user_uuid)
            status_code, content, error = response

        # Criar usuário local
        identity = MyfcidAPIBackend().create_local_identity(content)

        # 1 conta deve ter sido criada
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 3)

        # Autenticar o usuário
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            identity = MyfcidAPIBackend().authenticate(test_user_email, test_user_password)

        # A conta deve continuar existindo
        serviceAccountModel = get_account_module()
        accounts = serviceAccountModel.for_identity(identity)
        self.assertEquals(accounts.count(), 3)


class TestGetUser(TestCase):

    def _create_user(self):
        # Autenticar um usuário
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            return MyfcidAPIBackend().authenticate(test_user_email, test_user_password)


    def test_valid_user(self):
        identity = self._create_user()
        user = get_user(userid=identity.id)
        self.assertEquals(user, identity)


    def test_user_not_sent(self):
        user = get_user(userid=None)
        self.assertTrue(isinstance(user, AnonymousUser))


    def test_invalid_user(self):
        user = get_user(userid=42)
        self.assertTrue(isinstance(user, AnonymousUser))


class TestFetchUserData(TestCase):

    def test_fetch_user_data_with_success(self):
        with identity_client.tests.use_cassette('myfcid_api_backend/success'):
            _, user_data, _ = MyfcidAPIBackend().fetch_user_data(test_user_email, test_user_password)

        self.assertEquals(user_data, {
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

    def test_fetch_user_data_failure(self):
        with identity_client.tests.use_cassette('myfcid_api_backend/wrong_password'):
            _, user_data, error = MyfcidAPIBackend().fetch_user_data(test_user_email, 'senha errada')

        self.assertEquals(user_data, None)
        self.assertEquals(error, {'status': 401, 'message': '401 Client Error: UNAUTHORIZED'})
