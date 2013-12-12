#!/usr/bin/env python

from os.path import dirname, join
import sys
from optparse import OptionParser
import warnings


def parse_args():
    parser = OptionParser()
    parser.add_option('--use-tz', dest='USE_TZ', action='store_true')
    return parser.parse_args()


def configure_settings(options, PERSISTENCE_STRATEGY=None):
    from django.conf import settings

    # If DJANGO_SETTINGS_MODULE envvar exists the settings will be
    # configured by it. Otherwise it will use the parameters bellow.
    if not settings.configured:
        params = dict(
            PERSISTENCE_STRATEGY=PERSISTENCE_STRATEGY,
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            NOSQL_DATABASES = {
                'NAME': 'identity_client',
                'HOST': 'localhost',
            },
            INSTALLED_APPS = (
                'django.contrib.contenttypes',
                'identity_client',
            ),
            SITE_ID=1,
            TEST_RUNNER='django.test.simple.DjangoTestSuiteRunner',
            TEST_ROOT=join(dirname(__file__), 'identity_client', 'tests'),

            AUTHENTICATION_BACKENDS = ('identity_client.backend.MyfcidAPIBackend',),
            SERVICE_ACCOUNT_MODULE = 'identity_client.ServiceAccount',
            APPLICATION_HOST = 'http://testserver',
            LOGIN_REDIRECT_URL = '/developer/profile/',
            MYFC_ID = {
                'HOST': 'http://sandbox.app.passaporteweb.com.br',
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
        if getattr(options, 'USE_TZ', False):
            params.update(USE_TZ=True)
            warnings.filterwarnings('error', r"DateTimeField received a naive datetime",
                                    RuntimeWarning, r'django\.db\.models\.fields')

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
    if not labels:
        labels = ['generic']

    for PERSISTENCE_STRATEGY in ('django_db', 'mongoengine_db'):
        settings = configure_settings(options, PERSISTENCE_STRATEGY=PERSISTENCE_STRATEGY)
        runner = get_runner(settings)
        sys.exit(runner.run_tests(labels))


if __name__ == '__main__':
    options, labels = parse_args()
    runtests(options, labels)
