#!/usr/bin/env python

from os.path import dirname, join
import sys
from optparse import OptionParser
import warnings


def parse_args():
    parser = OptionParser()
    parser.add_option('--mongodb', action='store_true', dest='USE_MONGODB', default=False)
    parser.add_option('--sql', action='store_false', dest='USE_MONGODB')
    return parser.parse_args()


def configure_settings(options):
    from django.conf import settings

    # If DJANGO_SETTINGS_MODULE envvar exists the settings will be
    # configured by it. Otherwise it will use the parameters bellow.
    if not settings.configured:
        params = dict(
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': '',
                }
            },
            NOSQL_DATABASES = {
                'NAME': 'identity_client',
                'HOST': 'localhost',
            },
            INSTALLED_APPS = (
                'django.contrib.sessions',
                'identity_client',
            ),
            SITE_ID=1,
            TEST_RUNNER='django.test.simple.DjangoTestSuiteRunner',
            TEST_ROOT=join(dirname(__file__), 'identity_client', 'tests'),
            TEMPLATE_DIRS=(join(dirname(__file__), 'identity_client', 'tests', 'templates'), ),
            ROOT_URLCONF='identity_client.urls',

            TEMPLATE_CONTEXT_PROCESSORS = (
                'identity_client.processors.hosts',
            ),

            MIDDLEWARE_CLASSES = (
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'identity_client.middleware.P3PHeaderMiddleware',
            ),
            SESSION_SERIALIZER='django.contrib.sessions.serializers.PickleSerializer',

            AUTHENTICATION_BACKENDS = ('identity_client.backend.MyfcidAPIBackend',),
            SERVICE_ACCOUNT_MODULE = 'identity_client.ServiceAccount',
            APPLICATION_HOST = 'http://testserver',
            LOGIN_REDIRECT_URL = '/accounts/',
            PASSAPORTE_WEB = {
                'HOST': 'https://sandbox.app.passaporteweb.com.br',
                'SLUG': 'identity_client',
                'CONSUMER_TOKEN': 'qxRSNcIdeA',
                'CONSUMER_SECRET': '1f0AVCZPJbRndF9FNSGMOWMfH9KMUDaX',
                'AUTH_API':'accounts/api/auth/',
                'REGISTRATION_API':'accounts/api/create/',
                'PROFILE_API': 'profile/api/info/',
                'REQUEST_TOKEN_PATH':'sso/initiate/',
                'AUTHORIZATION_PATH':'sso/authorize/',
                'ACCESS_TOKEN_PATH':'sso/token/',
                'FETCH_USER_DATA_PATH':'sso/fetchuserdata/',
            },
        )

        # Force the use of timezone aware datetime and change Django's warning to
        # be treated as errors.
        if getattr(options, 'USE_MONGODB', False):
            params.update(PERSISTENCE_STRATEGY='mongoengine_db')
        else:
            params.update(PERSISTENCE_STRATEGY='django_db')

        # Configure Django's settings
        settings.configure(**params)

    return settings


def get_runner(settings):
    '''
    Asks Django for the TestRunner defined in settings or the default one.
    '''
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    return TestRunner(verbosity=1, interactive=True, failfast=False)


def runtests(options=None, labels=None):
    import django

    if not labels:
        labels = ['identity_client']

    settings = configure_settings(options)
    runner = get_runner(settings)
    if django.VERSION >= (1, 7):
        django.setup()
    sys.exit(runner.run_tests(labels))

if __name__ == '__main__':
    options, labels = parse_args()
    runtests(options, labels)
