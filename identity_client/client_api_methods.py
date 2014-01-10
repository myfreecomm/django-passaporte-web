# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime, date

import requests
from passaporte_web.main import Application, Identity as RemoteIdentity
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

    @classmethod
    @handle_api_exceptions_with_form
    def invoke_registration_api(cls, form):
        current_app = Application(host=cls.api_host, token=cls.api_user, secret=cls.api_password)
        logging.info(u'Trying to create user "{0}"'.format(form.cleaned_data.get('email', 'no email set')))
        user = current_app.users.create(**form.cleaned_data)
        return user.response.status_code, user.response.json()

    @classmethod
    @handle_api_exceptions
    def fetch_identity_data(cls, **kwargs):
        current_app = Application(host=cls.api_host, token=cls.api_user, secret=cls.api_password)
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
        current_app = Application(host=cls.api_host, token=cls.api_user, secret=cls.api_password)
        logging.info(u'Trying to fetch user with params "{0}"'.format(kwargs))
        user = current_app.users.get(uuid=uuid)

        logging.info(u'Fetching all accounts for user "{0}"'.format(user.uuid))
        kwargs['load_options'] = False
        user_accounts = [item.resource_data for item in user.accounts.all(**kwargs)]

        return 200, user_accounts

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

        account_data = json.dumps(account_data)

        url = '{0}/organizations/api/identities/{1}/accounts/'.format(cls.api_host, uuid)
        logging.info('create_user_account: Making request to %s', url)

        response = cls.pweb.post(
            url,
            headers={'content-length': str(len(account_data))},
            data=account_data
        )

        if response.status_code not in (200, 201):
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def fetch_account_data(cls, account_uuid):
        current_app = Application(host=cls.api_host, token=cls.api_user, secret=cls.api_password)
        logging.info(u'Trying to account with uuid "{0}"'.format(account_uuid))
        account = current_app.accounts.get(account_uuid)
        return account.response.status_code, account.response.json()

    @classmethod
    @handle_api_exceptions
    def update_account_data(cls, plan_slug, expiration, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        if isinstance(expiration, datetime):
            raise TypeError(u'expiration must be a date instance or None')
        elif isinstance(expiration, date):
            expiration = expiration.isoformat()
        elif expiration is not None:
            raise TypeError(u'expiration must be a date instance or None')

        account_data = json.dumps({'plan_slug': plan_slug, 'expiration': expiration})

        logging.info('update_account_data: Making request to %s', url)
        response = cls.pweb.put(
            url,
            headers={'content-length': str(len(account_data))},
            data=account_data
        )

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def add_account_member(cls, user_uuid, roles, api_path):

        if not isinstance(roles, list):
            raise TypeError(u"roles must be a list")

        member_data = json.dumps({'identity': user_uuid, 'roles': roles})

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('add_account_member: Making request to %s', url)

        response = cls.pweb.post(
            url,
            headers={'content-length': str(len(member_data))},
            data=member_data
        )

        if response.status_code not in (200, 201):
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def update_member_roles(cls, roles, api_path):

        if not isinstance(roles, list):
            raise TypeError(u"roles must be a list")

        member_data = json.dumps({'roles': roles})

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('update_member_roles: Making request to %s', url)

        response = cls.pweb.put(
            url,
            headers={'content-length': str(len(member_data))},
            data=member_data
        )

        if response.status_code != 200:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.json()


    @classmethod
    @handle_api_exceptions
    def remove_account_member(cls, api_path):

        if api_path.startswith(cls.api_host):
            url = api_path
        else:
            url = "{0}{1}".format(cls.api_host, api_path)

        logging.info('remove_account_member: Making request to %s', url)

        response = cls.pweb.delete(url)

        if response.status_code != 204:
            response.raise_for_status()
            raise requests.exceptions.HTTPError('Unexpected response', response=response)

        return response.status_code, response.text
