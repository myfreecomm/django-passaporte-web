# -*- coding: utf-8 -*-
import logging
import json
from httplib2 import HttpLib2Error

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext

from identity_client.sso.client import SSOClient
from identity_client.sso.decorators import oauth_callback
from identity_client.backend import MyfcidAPIBackend
from identity_client.views import login_user


__all__ = ['initiate', 'fetch_user_data']


def handle_api_exception(view):
    def func(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except HttpLib2Error, e:
            logging.error(
                '%s: Error during http request: %s<%s>',
                view.__name__,  e, type(e)
            )
            return HttpResponseServerError(status=502)
        except (AssertionError, ), e:
            logging.error(
                '%s: Unexpected status code %s<%s>',
                view.__name__, e, type(e)
            )
            return HttpResponseServerError()
    func.__name__ = view.__name__
    func.__doc__  = view.__doc__
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

    try:
        authorization_url = SSOClient().authorize(request)

        session_key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, None)
        logging.debug("Session %s data: %s", session_key, request.session.items())

    except AssertionError, e:
        resp, content = e.args

        message = "Could not fetch request token. Response was {0} - {1}".format(
            resp.get('status'), content
        )
        logging.error(message)
        return HttpResponseServerError(content=message)

    except ValueError, e:
        message = "Invalid request token"
        logging.error(message)
        return HttpResponseServerError(content=message)

    return HttpResponseRedirect(authorization_url)


@handle_api_exception
@oauth_callback
def fetch_user_data(request):

    try:
        resp, raw_user_data = SSOClient(request.access_token).post(SSOClient.user_data_url)

        if not str(resp.get('status')) == '200':
            raise AssertionError(resp, raw_user_data)

        identity = json.loads(
            raw_user_data, object_hook=as_local_identity
        )
        login_user(request, identity)

    except AssertionError, e:
        resp, content = e.args

        message = "Could not fetch user data. Response was {0} - {1}".format(
            resp.get('status'), content
        )
        logging.error(message)
        return HttpResponseServerError(content=message)

    except ValueError, e:
        message = "Invalid user data: {0}".format(raw_user_data)
        logging.error(message)
        return HttpResponseServerError(content=message)

    next_url = request.session.get('next_url', settings.LOGIN_REDIRECT_URL)

    return HttpResponseRedirect(next_url)


def as_local_identity(data):

    if ('uuid' in data) and ('email' in data):
        return MyfcidAPIBackend().create_local_identity(data)

    return data
