#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

COUNELL_LOG_FILE = '/tmp/counell.log'
COUCH_SERVER = 'http://localhost:5984/'
COUCH_DB = 'cc_sms'
COUCH_KANNEL_VIEW = 'cc/kannel'
COUCH_SMS_VIEW = 'cc/rapidsms'
COUCH_PID_FILE = '/var/run/couchdb/couchdb.pid'
COUCH_CHECK_INTERVAL = 20
KANOUCHD_PORT = 8090
KANNEL_SERVER = 'localhost'
KANNEL_PORT = 13001
KANNEL_USERNAME = 'kannel'
KANNEL_PASSWORD = 'kannel'
KANNEL_CHARSET = 'utf-8'
KANNEL_CODING = 2


# create a local_config.py file to override default values
try:
    from local_config import *
except ImportError:
    pass

KANNEL_SERVER_STRING = '%s:%s' % (KANNEL_SERVER, KANNEL_PORT)
KANNEL_PATH = "/cgi-bin/sendsms?username=" \
             "%(username)s&password=%(password)s" \
             "&charset=%(charset)s&coding=%(coding)s" \
             "&to=%(identity)s&text=%(text)s" \
             % {'username': KANNEL_USERNAME, 'password': KANNEL_PASSWORD, \
                'identity': '%(identity)s', 'text': '%(text)s', \
                'charset': KANNEL_CHARSET, 'coding': KANNEL_CODING}
KANNEL_URL = "http://%s%s" % (KANNEL_SERVER_STRING, KANNEL_PATH)
