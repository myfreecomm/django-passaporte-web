# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from passaporte_web.main import ServiceAccount as RemoteServiceAccount

from mongoengine import *
from mongoengine.queryset import Q

from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import SiteProfileNotAvailable

from identity_client.client_api_methods import APIClient
from identity_client.decorators import asyncmethod

class Identity(Document):
    """
    Myfc ID Users within the Django authentication system are represented by
    this model.

    email is required. Other fields are optional.
    """
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=100)
    email = StringField()
    uuid = StringField(max_length=36, unique=True)
    id_token = StringField(max_length=48, default=None)
    is_active = BooleanField(default=False)

    meta = {'allow_inheritance': True}

    def __unicode__(self):
        return self.email

    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def is_staff(self):
        """
        Always returns False.
        """
        return False

    def get_full_name(self):
        "Returns the first_name plus the last_name, with a space in between."
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def set_password(self, raw_password):
        raise NotImplementedError

    def check_password(self, raw_password):
        raise NotImplementedError

    def set_unusable_password(self):
        raise NotImplementedError

    def has_usable_password(self):
        return False

    def get_and_delete_messages(self):
        messages = []
        for m in self.message_set.all():
            messages.append(m.message)
            m.delete()
        return messages

    def email_user(self, subject, message, from_email=None):
        "Sends an e-mail to this User."
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email])

    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings
            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
                model = models.get_model(app_label, model_name)
                self._profile_cache = model._default_manager.using(self._state.db).get(user__id__exact=self.id)
                self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache

    def _get_message_set(self):
        import warnings
        warnings.warn('The user messaging API is deprecated. Please update'
                      ' your code to use the new messages framework.',
                      category=PendingDeprecationWarning)
        return self._message_set
    message_set = property(_get_message_set)


class AccountMember(EmbeddedDocument):
    identity = ReferenceField(Identity, required=True, dbref=True)
    roles = ListField(StringField(max_length=36))

    def set_roles(self, roles):
        roles = set(roles)
        self.roles = list(roles)

    def __unicode__(self):
        return u'%s - [%s]' % (self.identity.email, ','.join(self.roles))


class ServiceAccount(Document):
    name = StringField(max_length=256, required=True)
    uuid = StringField(max_length=36, required=True)
    plan_slug = StringField(max_length=50, required=True)
    members = ListField(EmbeddedDocumentField(AccountMember))
    expiration = DateTimeField(required=False)
    url = StringField(max_length=1024, required=False)

    meta = {'allow_inheritance': True}

    def __unicode__(self):
        return self.name

    @queryset_manager
    def active(cls, qset):
        return qset.filter(Q(expiration=None)|Q(expiration__gte=datetime.now()))

    @classmethod
    def for_identity(cls, identity, include_expired=False):
        if include_expired:
            qset = cls.objects
        else:
            qset = cls.active

        return qset.filter(members__identity=identity)

    @classmethod
    def refresh_accounts(cls, identity, **kwargs):

        accounts = cls.pull_remote_accounts(identity, **kwargs)
        cls.update_user_accounts(identity, accounts)
        cls.remove_stale_accounts(identity, accounts)

    @classmethod
    def pull_remote_accounts(cls, identity, **kwargs):
        status_code, accounts, error = APIClient.fetch_user_accounts(identity.uuid, **kwargs)

        default_roles = []
        if 'role' in kwargs:
            default_roles.append(kwargs['role'])

        if error:
            return []
        else:
            return [dict(
                uuid = item.get('account_data', item)['uuid'],
                name = item.get('account_data', item)['name'],
                expiration = item.get('expiration'),
                plan_slug = item.get('plan_slug', 'UNKNOWN'),
                url = item.get('url'),
                roles = item.get('roles', default_roles),
            ) for item in accounts]

    @classmethod
    def update_user_accounts(cls, identity, accounts):
        for item in accounts:
            uuid = item['uuid']
            name = item['name']
            expiration = item.get('expiration')
            plan_slug = item['plan_slug']
            url = item['url']
            roles = item['roles']

            try:
                account = cls.objects.get(uuid=uuid)
            except cls.DoesNotExist:
                account = cls(uuid=uuid)

            account.name = name
            account.plan_slug = plan_slug
            account.url = url

            if expiration:
                new_expiration = datetime.strptime(expiration, '%Y-%m-%d')
                account.update_expiration(new_expiration)
            else:
                account.update_expiration(None)

            try:
                account.add_member(identity, roles)
                account.save()
            except Exception, e:
                message = 'Error updating accounts for identity %s (%s): %s <%s>'
                logging.error(message, identity.email, identity.uuid, e, type(e))

            message = 'Identity %s (%s) at account %s (%s) members list'
            logging.info(message, identity.email, identity.uuid, account.name, account.uuid)

    @classmethod
    def remove_stale_accounts(cls, identity, accounts):
        current_uuids = [item['uuid'] for item in accounts]

        cached_associations = cls.for_identity(identity, include_expired=True)
        stale_accounts = [account for account in cached_associations if account.uuid not in current_uuids]

        for account in stale_accounts:
            account.remove_member(identity)
            account.save()
            message = 'Identity %s (%s) was removed from account %s (%s) members list.'
            logging.info(message, identity.email, identity.uuid, account.name, account.uuid)

    @property
    def is_active(self):
        return (self.expiration is None) or (self.expiration >= datetime.now())

    @property
    def members_count(self):
        return len(self.members)

    def get_member(self, identity):
        for item in self.members:
            if item.identity == identity:
                return item

        return None

    def add_member(self, identity, roles):
        new_member = self.get_member(identity)
        if new_member is None:
            new_member = AccountMember(identity=identity)
            self.members.append(new_member)

        new_member.set_roles(roles)
        self.save()

        return new_member

    def remove_member(self, identity):
        member = self.get_member(identity)
        if member is None:
            return self

        self.members.remove(member)
        self.save()

        return self

    def clear_members(self):
        self.members = []
        self.save()

    def update_expiration(self, new_expiration):
        self.expiration = new_expiration

    @asyncmethod
    def send_notification(self, body, **kwargs):
        return RemoteServiceAccount.load(
            self.url, token=APIClient.api_user, secret=APIClient.api_password
        ).send_notification(body, **kwargs)
