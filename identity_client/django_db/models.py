# -*- coding: utf-8 -*-
import logging

from datetime import datetime
from passaporte_web.main import ServiceAccount as RemoteServiceAccount

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from identity_client.client_api_methods import APIClient
from identity_client.decorators import asyncmethod


class Identity(models.Model):
    """
    Myfc ID Users within the Django authentication system are represented by
    this model.

    email is required. Other fields are optional.
    """
    first_name = models.CharField(_('first name'), max_length=50, null=True)
    last_name = models.CharField(_('last name'), max_length=100, null=True)
    email = models.EmailField(_('e-mail address'), unique=False)
    uuid = models.CharField(_('universally unique id'), max_length=36, unique=True)
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_("Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    )
    last_login = models.DateTimeField(_('last login'), default=datetime.now)

    class Meta:
        verbose_name = 'usuário do passaporte web'
        verbose_name_plural = u'usuários do passaporte web'
        app_label = 'identity_client'

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

    def get_full_name(self):
        "Returns the first_name plus the last_name, with a space in between."
        full_name = u'%s %s' % (self.first_name, self.last_name)
        if full_name.strip() == '':
            full_name = self.email

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


    def get_and_delete_messages(self):
        return []


    def has_perm(self, perm, obj=None):
        return self.is_active


    def has_module_perms(self, app_label):
        return self.is_active and app_label in (
            'access_control',
            'ecommerce',
            'cobrebem',
            'pagseguro',
            'identity_client',
            'myfinance',
        )


    @property
    def is_staff(self):
        return (self.id is not None) and self.domains.exists()


class ServiceAccount(models.Model):
    name = models.CharField(max_length=256)
    uuid = models.CharField(max_length=36)
    plan_slug = models.CharField(max_length=50)
    members = models.ManyToManyField(Identity, through='AccountMember')
    expiration = models.DateTimeField(null=True)
    url = models.CharField(max_length=1024, null=True)

    class Meta:
        app_label = 'identity_client'
        verbose_name = 'conta do passaporte web'
        verbose_name_plural = u'contas do passaporte web'

    def __unicode__(self):
        return self.name

    @classmethod
    def active(cls):
        return cls.objects.filter(
            Q(expiration=None)|Q(expiration__gte=datetime.now())
        )

    @classmethod
    def for_identity(cls, identity, include_expired=False):
        if include_expired:
            qset = cls.objects
        else:
            qset = cls.active()

        return qset.filter(accountmember__identity=identity)

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
        return self.members.count()

    def get_member(self, identity):
        member_qset = AccountMember.objects.filter(identity=identity, account=self)
        if member_qset.exists():
            return member_qset[0]

        return None

    def add_member(self, identity, roles):
        self.save()
        new_member, created = AccountMember.objects.get_or_create(identity=identity, account=self)
        new_member.set_roles(roles)
        new_member.save()

        return new_member

    def remove_member(self, identity):
        member_qset = AccountMember.objects.filter(identity=identity, account=self)
        if member_qset.exists():
            member_qset.delete()

        return self

    def clear_members(self):
        if self.id is None:
            return

        self.members.clear()

    def update_expiration(self, new_expiration):
        self.expiration = new_expiration

    @asyncmethod
    def send_notification(self, body, **kwargs):
        return RemoteServiceAccount.load(
            self.url, token=APIClient.api_user, secret=APIClient.api_password
        ).send_notification(body, **kwargs)


class AccountMember(models.Model):
    identity = models.ForeignKey(Identity)
    account = models.ForeignKey(ServiceAccount)
    _roles = models.CharField(max_length=720)

    class Meta:
        app_label = 'identity_client'
        verbose_name = 'membro da conta do passaporte web'
        verbose_name_plural = u'membros de contas do passaporte web'

    def __unicode__(self):
        return u'%s - [%s]' % (self.identity.email, self._roles)

    def set_roles(self, roles):
        roles = set(roles)
        self._roles = ','.join(roles)

    @property
    def roles(self):
        if self._roles:
            return self._roles.split(',')
        else:
            return []
