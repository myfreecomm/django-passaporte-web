# -*- coding: utf-8 -*-
from requests_oauthlib import OAuth1Session

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

from ..utils import reverse_with_host

class SSOClient(OAuth1Session):

    request_token_url = '%(HOST)s/%(REQUEST_TOKEN_PATH)s' % settings.PASSAPORTE_WEB
    access_token_url = '%(HOST)s/%(ACCESS_TOKEN_PATH)s' % settings.PASSAPORTE_WEB
    authorization_url = '%(HOST)s/%(AUTHORIZATION_PATH)s' % settings.PASSAPORTE_WEB
    user_data_url = '%(HOST)s/%(FETCH_USER_DATA_PATH)s' % settings.PASSAPORTE_WEB

    def __init__(self, **kwargs):
        client_key = settings.PASSAPORTE_WEB['CONSUMER_TOKEN']
        client_secret = settings.PASSAPORTE_WEB['CONSUMER_SECRET']
        callback_uri = reverse_with_host('sso_consumer:callback')

        return super(SSOClient, self).__init__(
            client_key, client_secret=client_secret, callback_uri=callback_uri, **kwargs
        )

    def fetch_request_token(self, realm=None):
        return super(SSOClient, self).fetch_request_token(self.request_token_url, realm=realm)

    def authorize(self, request):
        request_token = self.fetch_request_token()

        request.session['request_token'] = {request_token.get('oauth_token'): request_token.get('oauth_token_secret')}
        request.session[REDIRECT_FIELD_NAME] = request.GET.get(REDIRECT_FIELD_NAME, settings.LOGIN_REDIRECT_URL)
        request.session.save()

        return '{0}?oauth_token={1}'.format(
            self.authorization_url, request_token.get('oauth_token')
        )

    def fetch_access_token(self):
        return super(SSOClient, self).fetch_access_token(self.access_token_url)
