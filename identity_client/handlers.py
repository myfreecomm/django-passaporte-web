# -*- coding: utf-8 -*-
from identity_client.signals import pre_identity_authentication
from identity_client.utils import get_account_module

def update_identity_accounts(sender, identity, user_data, **kwargs):

    serviceAccount = get_account_module()
    accounts = user_data.get('accounts', None)

    if (serviceAccount is not None) and (accounts is not None):
        serviceAccount.update_user_accounts(identity, accounts)

    return


def dissociate_old_identity_accounts(sender, identity, user_data, **kwargs):

    serviceAccount = get_account_module()
    accounts = user_data.get('accounts', None)

    if (serviceAccount is not None) and (accounts is not None):
        serviceAccount.remove_stale_accounts(identity, accounts)

    return


pre_identity_authentication.connect(
    update_identity_accounts, dispatch_uid="update_identity_accounts"
)
pre_identity_authentication.connect(
    dissociate_old_identity_accounts, dispatch_uid="dissociate_old_identity_accounts"
)
