# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import requests
import futures

from mock import patch

from django.conf import settings

import identity_client
from identity_client import PERSISTENCE_MODULE
from identity_client.tests.helpers import MyfcIDTestCase as TestCase
from identity_client.models import Identity, ServiceAccount

__all__ = [
    'TestIdentityModel', 'TestServiceAccountModel'
]

mocked_accounts_json = '''[
    {
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Pessoal",
            "uuid": "e823f8e7-962c-414f-b63f-6cf439686159"
        },
        "plan_slug": "plus",
        "roles": ["owner"],
        "membership_details_url": "%s/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "%s/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
        "expiration": "%s",
        "external_id": null
    },
    {
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Myfreecomm",
            "uuid": "b39bad59-94af-4880-995a-04967b454c7a"
        },
        "plan_slug": "seller",
        "roles": ["owner"],
        "membership_details_url": "%s/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/members/1e73dad8-fefe-4b3a-a1a1-7149633748f2/",
        "url": "%s/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/",
        "expiration": "%s",
        "external_id": null
    },
    {
        "name": "Quebrando os testes",
        "uuid": "dab40435-45bc-45e1-b27e-f0a7c95739df"
    }
]''' % (
    settings.PASSAPORTE_WEB['HOST'],
    settings.PASSAPORTE_WEB['HOST'],
    (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
    settings.PASSAPORTE_WEB['HOST'],
    settings.PASSAPORTE_WEB['HOST'],
    (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d')
)

mocked_accounts_list = json.loads(mocked_accounts_json)


class TestIdentityModel(TestCase):


    def setUp(self):
        self.email=u'teste@email.com'
        self.identity = Identity(
            first_name='Teste',
            last_name='Sobrenome',
            email=self.email,
            uuid='16fd2706-8baf-433b-82eb-8c7fada847da',
        )


    def test_unicode(self):
        # An Identity should always be authenticated
        self.assertEquals(unicode(self.identity), self.email)


    def test_always_authenticated(self):
        # An Identity should always be authenticated
        self.assertTrue(self.identity.is_authenticated())


    def test_never_anonymous(self):
        # An Identity should never be anonymous
        self.assertEquals(self.identity.is_anonymous(), False)


    def test_set_password_not_implemented(self):
        # This method should not be implemented
        self.assertRaises(
            NotImplementedError,
            self.identity.set_password,
            's3nH4'
        )


    def test_check_password_not_implemented(self):
        # This method should not be implemented
        self.assertRaises(
            NotImplementedError,
            self.identity.check_password,
            's3nH4'
        )


    def test_set_unusable_password_not_implemented(self):
        # This method should not be implemented
        self.assertRaises(
            NotImplementedError,
            self.identity.set_unusable_password,
        )



    def test_has_usable_password_always_false(self):
        # An Identity should never have a usable password
        self.assertEquals(self.identity.has_usable_password(), False)


class TestServiceAccountModel(TestCase):

    def setUp(self):
        self.email = u'teste@email.com'
        self.identity = Identity.objects.create(
            first_name = 'Teste',
            last_name = 'Sobrenome',
            email = self.email,
            uuid = '16fd2706-8baf-433b-82eb-8c7fada847da',
        )

        self.account_name = 'Test Account'
        self.account = ServiceAccount.objects.create(
            name = self.account_name,
            uuid = '16fd2706-8baf-433b-82eb-8c7fada847da',
            plan_slug = 'platinum-test-plan',
        )


    def test_unicode(self):
        # An Identity should always be authenticated
        self.assertEquals(unicode(self.account), self.account_name)


    def test_account_without_expiration_is_active(self):
        self.assertEqual(self.account.expiration, None)
        self.assertTrue(self.account.is_active)


    def test_account_with_expiration_in_the_future_is_active(self):
        self.account.expiration = datetime.today() + timedelta(days=2)
        self.assertTrue(self.account.is_active)


    def test_account_with_expiration_in_the_past_is_not_active(self):
        self.account.expiration = datetime.today() - timedelta(days=2)
        self.assertFalse(self.account.is_active)


    def test_default_members_count_is_zero(self):
        self.assertEqual(self.account.members_count, 0)


    def test_add_member_to_empty_account(self):
        self.account.add_member(self.identity, roles=['user'])
        self.assertEqual(self.account.members_count, 1)


    def test_add_member_who_is_already_a_member_does_not_change_member_count(self):
        self.account.add_member(self.identity, roles=['user'])
        self.account.add_member(self.identity, roles=['user', 'admin'])
        self.assertEqual(self.account.members_count, 1)


    def test_get_member_returns_accountmember(self):
        self.account.add_member(self.identity, roles=['user'])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.identity, self.identity)
        self.assertEqual(member.roles, ['user'])


    def test_get_non_existing_member_returns_none(self):
        member = self.account.get_member(self.identity)
        self.assertEqual(member, None)


    def test_get_member_roles_is_a_list_of_strings(self):
        self.account.add_member(self.identity, roles=['user', 'admin'])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.roles, ['admin', 'user'])


    def test_add_member_who_is_already_a_member_overwrites_roles(self):
        self.account.add_member(self.identity, roles=['user'])
        self.account.add_member(self.identity, roles=['user', 'admin'])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.roles, ['admin', 'user'])


    def test_member_may_have_no_roles(self):
        self.account.add_member(self.identity, roles=[])
        member = self.account.get_member(self.identity)
        self.assertEqual(member.roles, [])


    def test_remove_member_returns_account(self):
        self.account.add_member(self.identity, roles=['user'])
        account = self.account.remove_member(self.identity)
        self.assertEqual(account, self.account)
        self.assertEqual(account.members_count, 0)


    def test_remove_non_existing_member_fails_silently(self):
        account = self.account.remove_member(self.identity)
        self.assertEqual(account, self.account)
        self.assertEqual(account.members_count, 0)


    def test_account_without_expiration_is_active(self):
        self.assertEqual(self.account.expiration, None)
        active_accounts = ServiceAccount.active().all()
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    def test_account_with_expiration_in_the_future_is_active(self):
        self.account.expiration = datetime.today() + timedelta(days=2)
        self.account.save()
        active_accounts = ServiceAccount.active().all()
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    def test_account_with_expiration_in_the_past_is_not_active(self):
        self.account.expiration = datetime.today() - timedelta(days=2)
        self.account.save()
        active_accounts = ServiceAccount.active().all()
        self.assertEqual(len(active_accounts), 0)


    def test_accounts_for_identity(self):
        self.account.add_member(self.identity, roles=['user'])
        active_accounts = ServiceAccount.for_identity(self.identity)
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    def test_accounts_for_identity_without_accounts_associated(self):
        active_accounts = ServiceAccount.for_identity(self.identity)
        self.assertEqual(len(active_accounts), 0)


    def test_accounts_for_identity_ignores_expired_accounts_by_default(self):
        self.account.expiration = datetime.today() - timedelta(days=2)
        self.account.add_member(self.identity, roles=[])

        active_accounts = ServiceAccount.for_identity(self.identity)
        self.assertEqual(len(active_accounts), 0)


    def test_accounts_for_identity_may_include_expired_accounts(self):
        self.account.expiration = datetime.today() - timedelta(days=2)
        self.account.add_member(self.identity, roles=[])

        active_accounts = ServiceAccount.for_identity(self.identity, include_expired=True)
        self.assertEqual(len(active_accounts), 1)
        self.assertEqual(active_accounts[0], self.account)


    @patch.object(PERSISTENCE_MODULE.models.APIClient, 'fetch_user_accounts')
    def test_pull_remote_accounts_changes_response_format(self, mocked_accounts):
        mocked_accounts.return_value = 200, mocked_accounts_list, []
        accounts = ServiceAccount.pull_remote_accounts(self.identity)

        expected = [
            {
                'plan_slug': mocked_accounts_list[0]['plan_slug'],
                'uuid': mocked_accounts_list[0]['account_data']['uuid'],
                'roles': mocked_accounts_list[0]['roles'],
                'url': mocked_accounts_list[0]['url'],
                'name': mocked_accounts_list[0]['account_data']['name'],
                'expiration': mocked_accounts_list[0]['expiration'],
            },
            {
                'plan_slug': mocked_accounts_list[1]['plan_slug'],
                'uuid': mocked_accounts_list[1]['account_data']['uuid'],
                'roles': mocked_accounts_list[1]['roles'],
                'url': mocked_accounts_list[1]['url'],
                'name': mocked_accounts_list[1]['account_data']['name'],
                'expiration': mocked_accounts_list[1]['expiration'],
            },
            {
                'plan_slug': 'UNKNOWN',
                'uuid': mocked_accounts_list[2]['uuid'],
                'roles': [],
                'url': None,
                'name': mocked_accounts_list[2]['name'],
                'expiration': None,
            },
        ]

        self.assertEqual(list(accounts), expected)


    @patch.object(PERSISTENCE_MODULE.models.APIClient, 'fetch_user_accounts')
    def test_update_user_accounts_creates_local_accounts(self, mocked_accounts):
        mocked_accounts.return_value = 200, mocked_accounts_list, []

        self.assertEquals(ServiceAccount.for_identity(self.identity).count(), 0)

        accounts = ServiceAccount.pull_remote_accounts(self.identity)
        ServiceAccount.update_user_accounts(self.identity, accounts)

        self.assertEquals(ServiceAccount.for_identity(self.identity).count(), 3)


    @patch.object(PERSISTENCE_MODULE.models.APIClient, 'fetch_user_accounts')
    def test_remove_stale_accounts(self, mocked_accounts):
        mocked_accounts.return_value = 200, mocked_accounts_list, []

        self.account.add_member(self.identity, roles=['user'])
        self.assertEquals(ServiceAccount.for_identity(self.identity).count(), 1)

        accounts = ServiceAccount.pull_remote_accounts(self.identity)
        ServiceAccount.remove_stale_accounts(self.identity, accounts)

        self.assertEquals(ServiceAccount.for_identity(self.identity).count(), 0)


    @patch.object(PERSISTENCE_MODULE.models.APIClient, 'fetch_user_accounts')
    def test_refresh_user_accounts(self, mocked_accounts):
        """
        This method reads the remote user's accounts,
        updates them locally and purges the accounts which do not exist anymore.
        """
        mocked_accounts.return_value = 200, mocked_accounts_list, []

        self.account.add_member(self.identity, roles=['user'])
        self.assertEquals(ServiceAccount.for_identity(self.identity).count(), 1)

        ServiceAccount.refresh_accounts(self.identity)

        self.assertEquals(ServiceAccount.for_identity(self.identity).count(), 3)
        self.assertFalse(self.account in ServiceAccount.for_identity(self.identity))

    def test_send_notification(self):
        self.account.url = "http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/"
        body = "Test notification for the account"
        with identity_client.tests.use_cassette('service_account/send_notification'):
            future = self.account.send_notification(body)

        self.assertTrue(isinstance(future, futures.Future))
        self.assertEquals(future.result().body, body)

    def test_error_sending_notification(self):
        self.account.url = "http://sandbox.app.passaporteweb.com.br/organizations/api/accounts/e5ab6f2f-a4eb-431b-8c12-9411fd8a872d/"
        body = "Test notification for the account"
        with identity_client.tests.use_cassette('service_account/403_sending_notification'):
            # The call won't fail
            future = self.account.send_notification(body)

        # Buy the result will contain the raised exception
        self.assertTrue(isinstance(future, futures.Future))
        self.assertRaises(requests.HTTPError, future.result)
