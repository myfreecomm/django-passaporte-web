#-*- coding: utf-8 -*-
import logging
from functools import wraps

import futures
import requests
from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test
from django.template import Context, loader

from identity_client.utils import get_account_module
from identity_client.utils import prepare_form_errors


__all__ = [
    'required_method', 'sso_login_required', 'requires_plan', 'with_403_page',
    'handle_api_exceptions', 'handle_api_exceptions_with_form',
]


class required_method(object):

    def __init__(self, *args, **kwargs):
        self.methods = args
        self.error = kwargs.get('error',
            # Default error:
            http.HttpResponse('Not Implemented',
                mimetype='text/plain', status=501)
        )

    def __call__(self, view):
        def f(request, *args, **kwargs):
            if request.method in self.methods:
                return view(request, *args, **kwargs)
            else:
                return self.error
        f.__name__ = view.__name__
        f.__doc__ = view.__doc__
        return f


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


def requires_plan(plan_slug):

    def decorator(view):

        @sso_login_required
        def check_user_plan(request, *args, **kwargs):
            """
            Este decorator assume que a autenticação acabou de ser feita,
            portanto as contas do usuário estão sincronizadas com o Passaporte Web.
            """
            serviceAccount = get_account_module()
            user_accounts = serviceAccount.for_identity(request.user)
            required_plan_accounts = user_accounts.filter(plan_slug=plan_slug)

            if required_plan_accounts.count() > 0:
                return view(request, *args, **kwargs)
            else:
                logging.info(
                    'Request from user %s (uuid=%s) denied (%s). User has no accounts at plan "%s".',
                    request.user.email,
                    request.user.uuid,
                    request.path,
                    plan_slug,
                )
                return http.HttpResponseForbidden()

        return check_user_plan
        
    return decorator


def with_403_page(view):

    # You need to create a 403.html template.
    template_name = '403.html'

    def handle_403(request, *args, **kwargs):
        response = view(request, *args, **kwargs)

        if isinstance(response, http.HttpResponseForbidden):
            t = loader.get_template(template_name) 
            response = http.HttpResponseForbidden(
                t.render(
                    Context({'MEDIA_URL': settings.MEDIA_URL})
                )
            )

        return response

    return handle_403


def handle_api_exceptions(method):

    @wraps(method)
    def handler(cls, *args, **kwargs):
        status_code = 500
        content = error = None

        try:
            status_code, content = method(cls, *args, **kwargs)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error = {
                'status': e.response.status_code,
                'message': e.response.text if e.response.text else e.message,
            }

        except requests.exceptions.ConnectionError as e:
            error = {
                'status': None,
                'message': 'Error connecting to PassaporteWeb',
            }

        except requests.exceptions.Timeout as e:
            error = {
                'status': None,
                'message': 'Timeout connecting to PassaporteWeb',
            }

        except (requests.exceptions.RequestException, Exception) as e:
            error = {
                'status': None,
                'message': u'Unexpected error: {0} <{1}>'.format(e, type(e)),
            }

        if error:
            logging.error(
                'fetch_identity_data: Error making request: %s - %s',
                error['status'], error['message']
            )

        return (status_code, content, error)

    return handler


def handle_api_exceptions_with_form(method):

    @wraps(method)
    def handler(cls, form, *args, **kwargs):
        status_code = 500
        content = error = error_dict = None

        try:
            status_code, content = method(cls, form, *args, **kwargs)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            if e.response.status_code in (400, 409):
                error_dict = e.response.json()
            else:
                error_dict = {
                    '__all__': [error_messages.get(e.response.status_code, error_messages['default']), ]
                }

            error = {
                'status': e.response.status_code,
                'message': e.response.text if e.response.text else e.message,
            }

        except requests.exceptions.ConnectionError as e:
            error_dict = {
                '__all__': [error_messages.get('ConnectionError', error_messages['default']), ]
            }
            error = {
                'status': None,
                'message': 'Error connecting to passaporteweb',
            }

        except requests.exceptions.Timeout as e:
            error_dict = {
                '__all__': [error_messages.get('Timeout', error_messages['default']), ]
            }
            error = {
                'status': None,
                'message': 'Timeout connecting to passaporteweb',
            }

        except (requests.exceptions.RequestException, Exception) as e:
            error_dict = {
                '__all__': [error_messages.get('default'), ]
            }
            error = {
                'status': None,
                'message': u'Unexpected error: {0} <{1}>'.format(e, type(e)),
            }

        if error_dict:
            form._errors = prepare_form_errors(error_dict)

        if error:
            logging.error(
                '%s: Error making request: %s - %s',
                method.__name__, error['status'], error['message']
            )

        return (status_code, content, form)

    return handler


def asyncmethod(method):

    def callback(future):
        try:
            result = future.result()
            return result
        except Exception as e:
            logging.error(
                'asyncmethod: Future "%s" raised an exception: "%s" (%s)',
                future, e, type(e)
            )

    @wraps(method)
    def handler(*args, **kwargs):
        logging.info(
            'asyncmethod: Method "%s" invoked with args "%s" and kwargs "%s"',
            method.__name__, args, kwargs
        )
        with futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_result = executor.submit(method, *args, **kwargs)
            future_result.add_done_callback(callback)

        return future_result

    return handler


error_messages = {
    401: u"Esta aplicação não está autorizada a utilizar o PassaporteWeb. Entre em contato com o suporte.",
    400: u"Erro na transmissão dos dados. Tente novamente.",
    409: u"Email já cadastrado.",
    'ConnectionError': u"Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.",
    'Timeout': u"Ocorreu uma falha na comunicação com o Passaporte Web. Por favor tente novamente.",
    'default': u"Erro no servidor. Entre em contato com o suporte.",
}
