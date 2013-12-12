# -*- coding: utf-8 -*-
import logging
import oauth2 as oauth
from httplib2 import HttpLib2Error

from django.http import HttpResponseServerError, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings

from identity_client.sso.client import SSOClient


__all__ = ['oauth_callback', ]


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
                secret = request_token[oauth_token]

                request_token = oauth.Token(key=oauth_token, secret=secret)
                request_token.set_verifier(oauth_verifier)

                try:
                    # Adicionar access token à sessão
                    access_token = SSOClient(request_token).fetch_access_token()
                    request.session['access_token'] = {
                        access_token.key: access_token.secret
                    }
                    request.session.save()

                    # E à request
                    request.access_token = access_token

                except AssertionError, e:
                    resp, content = e.args

                    message = "Could not fetch access token. Response was {0} - {1}".format(
                        resp.get('status'), content
                    )
                    logging.error(message)
                    return HttpResponseServerError(content=message)

                except ValueError, e:
                    message = "Invalid access token"
                    logging.error(message)
                    return HttpResponseServerError(content=message)

                except HttpLib2Error, e:
                    message = "Could not fetch access token, communication failure: {0} ({1})".format(
                        e, type(e)
                    )
                    logging.error(message)
                    return HttpResponseServerError(status=502, content=message)

                except Exception, e:
                    message = "Could not fetch access token, unknown error: {0} ({1})".format(
                        e, type(e)
                    )
                    logging.error(message)
                    return HttpResponseServerError(content=message)

            return view(request, *args, **kwargs)

    return decorated
