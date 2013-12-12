#coding:utf-8

from mock import Mock, patch

OAUTH_REQUEST_TOKEN = 'dummyrequesttoken'
OAUTH_REQUEST_TOKEN_SECRET = 'dummyrequesttokensecret'
OAUTH_ACCESS_TOKEN = 'dummyaccesstoken'
OAUTH_ACCESS_TOKEN_SECRET = 'dummyaccesstokensecret'

def patch_httplib2(new):
    return patch('httplib2.Http.request', new)

def mocked_request_token():
    content = '&'.join([
        'oauth_token_secret=%s' % OAUTH_REQUEST_TOKEN_SECRET,
        'oauth_token=%s' % OAUTH_REQUEST_TOKEN,
        'oauth_callback_confirmed=true'
    ])

    return mocked_response(200, content)

def mocked_access_token():
    content = '&'.join([
        'oauth_token_secret=%s' % OAUTH_ACCESS_TOKEN_SECRET,
        'oauth_token=%s' % OAUTH_ACCESS_TOKEN
    ])

    return mocked_response(200, content)

def mocked_response(status, content):
    response = {
        'status': status,
    }

    return response, content
