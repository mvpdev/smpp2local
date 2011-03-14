#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

COUCH_SERVER = 'http://localhost:5984/'
COUCH_DB = 'cc_sms'
KANOUCHD_PORT = 8090
KANNEL_SERVER = 'localhost'
KANNEL_PORT = 13001
KANNEL_USERNAME = 'kannel'
KANNEL_PASSWORD = 'kannel'
KANNEL_SERVER_STRING = '%s:%s' % (KANNEL_SERVER, KANNEL_PORT)
KANNEL_PATH = "/cgi-bin/sendsms?username=" \
             "%(username)s&password=%(password)s" \
             "&charset=utf-8&coding=2&to=%(identity)s&text=%(text)s" \
             % {'username': KANNEL_USERNAME, 'password': KANNEL_PASSWORD, \
                'identity': '%(identity)s', 'text': '%(text)s'}
KANNEL_URL = "http://%s%s" % (KANNEL_SERVER_STRING, KANNEL_PATH)

try:
    from local_config import *
except ImportError:
    pass
