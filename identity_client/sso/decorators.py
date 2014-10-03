# -*- coding: utf-8 -*-
import logging
import six
from requests.exceptions import ReadTimeout, RequestException
from requests_oauthlib.oauth1_session import TokenRequestDenied

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseServerError, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

from identity_client.sso.client import SSOClient


__all__ = ['sso_login_required', 'oauth_callback']


def sso_login_required(view):

    def decorated(request, *args, **kwargs):
        url = reverse('sso_consumer:request_token')

        actual_decorator = user_passes_test(
            lambda user: user.is_authenticated(),
            login_url=url,
        )

        wrapped_view = actual_decorator(view)

        return wrapped_view(request, *args, **kwargs)

    return decorated


def oauth_callback(view):

    def decorated(request, *args, **kwargs):
        if 'request_token' not in request.session:
            # O fluxo de autenticação ainda não foi iniciado

            # Salvar a url do callback na sessão, ignorando sua querystring
            request.session['callback_url'] = u'{0}{1}'.format(
                settings.APPLICATION_HOST, request.path
            )
            request.session.save()

            return HttpResponseRedirect(reverse('sso_consumer:request_token'))

        else:
            # O fluxo de autenticação já foi iniciado
            if  getattr(request, 'access_token', None) is None:
                # Obter access token
                oauth_token = request.GET.get('oauth_token')
                oauth_verifier = request.GET.get('oauth_verifier')

                request_token = request.session['request_token']
                oauth_secret = request_token[oauth_token]
                try:
                    # Adicionar access token à sessão
                    access_token = SSOClient(
                        resource_owner_key=oauth_token,
                        resource_owner_secret=oauth_secret,
                        verifier=oauth_verifier
                    ).fetch_access_token()
                    request.session['access_token'] = {
                        access_token['oauth_token']: access_token['oauth_token_secret']
                    }
                    request.session.save()

                    # E à request
                    request.access_token = {
                        'resource_owner_key': access_token['oauth_token'],
                        'resource_owner_secret': access_token['oauth_token_secret']
                    }

                except ReadTimeout as e:
                    message = e.args[0].args[0]
                    logging.error(message)
                    return HttpResponseServerError(content=message, status=503)

                except RequestException as e:
                    message = u"Could not fetch access token. {0} ({1})".format(e, e.response.text)
                    logging.error(message)
                    return HttpResponseServerError(content=message, status=503)

                except TokenRequestDenied as e:
                    message = u';'.join(e.args)
                    logging.error(message)
                    return HttpResponseServerError(content=message, status=503)

                except ValueError as e:
                    message = u"Could not fetch access token. {0}".format(e)
                    logging.error(message)
                    return HttpResponseServerError(content=message)

                except Exception as e:
                    message = u"Could not fetch access token. Unknown error ({0})".format(e)
                    logging.error(message)
                    return HttpResponseServerError(content=message)

            return view(request, *args, **kwargs)

    return decorated
