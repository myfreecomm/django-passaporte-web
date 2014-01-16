# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime, date

import requests
from passaporte_web.main import Application, Identity as RemoteIdentity, ServiceAccount as RemoteServiceAccount, AccountMembers, AccountMember
from django.conf import settings

from identity_client.decorators import handle_api_exceptions, handle_api_exceptions_with_form

__all__ = ['APIClient']

# TODO: 
# - fetch_application_accounts
# - perfil
# - notificações
#   - como tratar a paginação?


class APIClient(object):

    api_host = settings.PASSAPORTE_WEB['HOST']
    api_user = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
    api_password = settings.PASSAPORTE_WEB['CONSUMER_SECRET']
    profile_api = settings.PASSAPORTE_WEB['PROFILE_API']
    registration_api = settings.PASSAPORTE_WEB['REGISTRATION_API']

    pweb = requests.Session()
    pweb.auth = (api_user, api_password)
    pweb.headers.update({
        'cache-control': 'no-cache',
        'content-length': '0',
        'content-type': 'application/json',
        'accept': 'application/json',
        'user-agent': 'myfc_id client',
    })
    _application = None

    @classmethod
    def get_application(cls):
        is_same_app = lambda app: (app.token == cls.api_user) and \
             (app.secret == cls.api_password) and \
             (app.host == cls.api_host)

        if (cls._application is None) or not is_same_app(cls._application):
            cls._application = Application(host=cls.api_host, token=cls.api_user, secret=cls.api_password)

        return cls._application

    @classmethod
    @handle_api_exceptions_with_form
    def invoke_registration_api(cls, form):
        current_app = cls.get_application()
        logging.info(u'Trying to create user "{0}"'.format(form.cleaned_data.get('email', 'no email set')))
        user = current_app.users.create(**form.cleaned_data)
        return user.response.status_code, user.response.json()

    @classmethod
    @handle_api_exceptions
    def fetch_identity_data(cls, **kwargs):
        current_app = cls.get_application()
        logging.info(u'Trying to fetch user with params "{0}"'.format(kwargs))
        user = current_app.users.get(**kwargs)
        return user.response.status_code, user.response.json()

    @classmethod
    @handle_api_exceptions_with_form
    def update_user_api(cls, form, api_path):
        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info(u'Loading information for user identified by "{0}"'.format(url))
        remote_user = RemoteIdentity.load(url, token=cls.api_user, secret=cls.api_password)

        remote_user.resource_data.update(form.cleaned_data)
        logging.info(u'Updating information for user identified by "{0}"'.format(url))
        remote_user = remote_user.save()
        return remote_user.response.status_code, remote_user.response.json()

    @classmethod
    @handle_api_exceptions
    def fetch_association_data(cls, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('fetch_association_data: Making request to %s', url)
        response = cls.pweb.get(url)

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()

    @classmethod
    @handle_api_exceptions
    def update_association_data(cls, new_data, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('update_association_data: Making request to %s', url)

        association_data = json.dumps(new_data)
        response = cls.pweb.put(
                url,
                headers={'content-length': str(len(association_data))},
                data=association_data
        )

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()

    @classmethod
    @handle_api_exceptions
    def fetch_user_accounts(cls, uuid, **kwargs):
        current_app = cls.get_application()
        logging.info(u'Trying to fetch user with uuid "{0}"'.format(uuid))
        user = current_app.users.get(uuid=uuid)

        logging.info(u'Fetching all accounts for user "{0}"'.format(user.uuid))
        kwargs['load_options'] = False
        user_accounts = [item.resource_data for item in user.accounts.all(**kwargs)]

        return 200, user_accounts

    @classmethod
    @handle_api_exceptions
    def fetch_account_data(cls, account_uuid):
        current_app = cls.get_application()
        logging.info(u'Trying to account with uuid "{0}"'.format(account_uuid))
        account = current_app.accounts.get(account_uuid)
        return account.response.status_code, account.response.json()

    @classmethod
    @handle_api_exceptions
    def create_user_account(cls, uuid, plan_slug, account_uuid=None, account_name=None, expiration=None):
        account_data = {'plan_slug': plan_slug, 'expiration': expiration}
        if account_uuid:
            account_data['uuid'] = account_uuid
        elif account_name:
            account_data['name'] = account_name
        else:
            raise ValueError("Either 'account_uuid' or 'account_name' must be given")

        current_app = cls.get_application()
        logging.info(u'Trying to fetch user with uuid "{0}"'.format(uuid))
        user = current_app.users.get(uuid=uuid)

        logging.info(u'Creating account for user "{0}" with "{1}"'.format(uuid, account_data))
        new_account = user.accounts.create(**account_data)

        return new_account.response.status_code, new_account.response.json()

    @classmethod
    @handle_api_exceptions
    def update_account_data(cls, plan_slug, expiration, api_path):
        if isinstance(expiration, datetime):
            raise TypeError(u'expiration must be a date instance or None')
        elif isinstance(expiration, date):
            expiration = expiration.isoformat()
        elif expiration is not None:
            raise TypeError(u'expiration must be a date instance or None')

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info(u'Loading information for service account identified by "{0}"'.format(url))
        remote_account = RemoteServiceAccount.load(url, token=cls.api_user, secret=cls.api_password)
        remote_account.resource_data.update({'plan_slug': plan_slug, 'expiration': expiration})

        logging.info(u'Updating information for service account identified by "{0}"'.format(url))
        remote_account = remote_account.save()

        return remote_account.response.status_code, remote_account.response.json()

    @classmethod
    @handle_api_exceptions
    def add_account_member(cls, user_uuid, roles, api_path):
        if not isinstance(roles, list):
            raise TypeError(u"roles must be a list")

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        account_members = AccountMembers(url, token=cls.api_user, secret=cls.api_password)
        
        logging.info(u'Adding user with uuid "{0}" to account members identified by url "{1}"'.format(user_uuid, url))
        member = account_members.create(identity=user_uuid, roles=roles)

        return member.response.status_code, member.response.json()

    @classmethod
    @handle_api_exceptions
    def update_member_roles(cls, roles, api_path):
        if not isinstance(roles, (list, set)):
            raise TypeError(u"roles must be a list")

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info(u'Loading information for account member identified by "{0}"'.format(url))
        account_member = AccountMember.load(url, token=cls.api_user, secret=cls.api_password)
        account_member.roles = roles

        logging.info(u'Updating information for account member identified by "{0}"'.format(url))
        account_member = account_member.save()

        return account_member.response.status_code, account_member.response.json()

    @classmethod
    @handle_api_exceptions
    def remove_account_member(cls, api_path):
        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        account_member = AccountMember.load(url, token=cls.api_user, secret=cls.api_password)
        logging.info(u'Removing account member identified by "{0}"'.format(url))
        account_member.delete()

        return 204, ''
