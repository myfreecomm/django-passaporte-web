# -*- coding: utf-8 -*-
import logging
import six
from requests.exceptions import ReadTimeout, RequestException
from requests_oauthlib.oauth1_session import TokenRequestDenied

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import REDIRECT_FIELD_NAME

from identity_client.sso.client import SSOClient
from identity_client.sso.decorators import oauth_callback
from identity_client.backend import MyfcidAPIBackend
from identity_client.views import login_user


__all__ = ['initiate', 'fetch_user_data']


def handle_api_exception(view):
    @six.wraps(view)
    def func(*args, **kwargs):
        try:
            return view(*args, **kwargs)

        except ReadTimeout as e:
            message = u'Error invoking {0}: {1}'.format(view.__name__, e.args[0].args[0])
            logging.error(message)
            return HttpResponseServerError(content=message, status=503)

        except RequestException as e:
            message = u"Error invoking {0}: {1} ({2})".format(view.__name__, e, e.response.text)
            logging.error(message)
            return HttpResponseServerError(content=message, status=503)

        except TokenRequestDenied as e:
            message = u'Error invoking {0}: {1}'.format(view.__name__, u';'.join(e.args))
            logging.error(message)
            return HttpResponseServerError(content=message, status=503)

        except ValueError as e:
            message = u'Error invoking {0}: Unable to decode token from token response'.format(view.__name__)
            logging.error(message)
            return HttpResponseServerError(status=500)

        except Exception as e:
            message = u'Error invoking {0}: {1} {2}'.format(view.__name__, e, type(e))
            logging.error(message)
            return HttpResponseServerError(status=500)

    return func


def render_sso_iframe(request):
    context = {
        'myfcid_host': settings.PASSAPORTE_WEB['HOST'],
        'application_host': settings.APPLICATION_HOST,
        'application_slug': settings.PASSAPORTE_WEB['SLUG'],
    }

    return render_to_response(
        'sso_iframe.html',
        context,
        context_instance=RequestContext(request)
    )


@handle_api_exception
def initiate(request):
    authorization_url = SSOClient().authorize(request)

    session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
    logging.debug("Session %s data: %s", session_key, request.session.items())

    return HttpResponseRedirect(authorization_url)


@handle_api_exception
@oauth_callback
def fetch_user_data(request):
    try:
        sso_client = SSOClient(**request.access_token)
        response = sso_client.post(SSOClient.user_data_url)
        response.raise_for_status()

        identity = response.json(object_hook=as_local_identity)
        login_user(request, identity)

    except AssertionError as e:
        resp, content = e.args

        message = "Could not fetch user data. Response was {0} - {1}".format(
            resp.get('status'), content
        )
        logging.error(message)
        return HttpResponseServerError(content=message)

    except ValueError as e:
        message = "Invalid user data: {0}".format(raw_user_data)
        logging.error(message)
        return HttpResponseServerError(content=message)

    next_url = request.session.get(REDIRECT_FIELD_NAME, settings.LOGIN_REDIRECT_URL)

    return HttpResponseRedirect(next_url)


def as_local_identity(data):
    if ('uuid' in data) and ('email' in data):
        return MyfcidAPIBackend().create_local_identity(data)

    return data
