=====================
django-passaporte-web
=====================

Sobre o Passaporte Web
----------------------

O Passaporte Web é um ecossistema de aplicações corporativas que disponibiliza uma série de funcionalidades para
simplificar a implementação, operação e comercialização de suas aplicações; com o objetivo de possibilitar que você
se preocupe somente com o desenvolmento das funções diretamente relacionadas aos objetivos de sua aplicação.

Nosso objetivo é construir uma comunidade de desenvolvedores e aplicações de altíssima qualidade.

O Passaporte Web oferece:
    - Mecanismos de cadastro de usuários, autenticação e controle de acesso centralizado;
    - Ferramentas para gestão de usuários, vendas, pagamentos, aplicações e controle de acesso aos sistemas e às APIs;
    - Sistema de venda de acesso às aplicações, com suporte a múltiplos meios de pagamento e cobrança recorrente;
    - Mecanismos para simplificar a integração entre aplicações do ecossistema;
    - Ambientes de homologação (sandbox) para auxiliar o desenvolvimento e evolução de sua aplicação;


Configurações necessárias
-------------------------

.. code-block:: python

    INSTALLED_APPS += (
        'identity_client',
    )
    TEMPLATE_CONTEXT_PROCESSORS += (
        'identity_client.processors.hosts',
    )
    MIDDLEWARE_CLASSES += (
        'identity_client.middleware.P3PHeaderMiddleware',
    )

    APPLICATION_HOST = '<protocol>://<host>'
    PERSISTENCE_STRATEGY = 'django_db' ou 'mongoengine_db'
    AUTHENTICATION_BACKENDS = ('identity_client.backend.MyfcidAPIBackend',)
    SERVICE_ACCOUNT_MODULE = 'identity_client.ServiceAccount'
    PASSAPORTE_WEB = {
        'HOST': 'http://sandbox.app.passaporteweb.com.br',
        'SLUG': <slug da sua aplicação>,
        'CONSUMER_TOKEN': <token de uma instância da sua aplicação>,
        'CONSUMER_SECRET': <secret de uma instância da sua aplicação>,
        'AUTH_API': 'accounts/api/auth/',
        'REGISTRATION_API': 'accounts/api/create/',
        'PROFILE_API': 'profile/api/info/',
        'REQUEST_TOKEN_PATH': 'sso/initiate/',
        'AUTHORIZATION_PATH': 'sso/authorize/',
        'ACCESS_TOKEN_PATH': 'sso/token/',
        'FETCH_USER_DATA_PATH': 'sso/fetchuserdata/',
    }

    if PERSISTENCE_STRATEGY == 'mongoengine_db':
        SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer' # django >= 1.6
        NOSQL_DATABASES = {
            'NAME': '<db name>',
            'HOST': '<db host>',
        }
