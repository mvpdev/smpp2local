#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

''' webserver expecting identity and text to store incoming sms in CouchDB '''

import sys
from datetime import datetime

import cherrypy
import couchdb

from config import *

couch = couchdb.Server(COUCH_SERVER)
database = couch[COUCH_DB]


def document_from_sms(identity, text, date=datetime.now()):
    document = {'identity': identity,
                'datetime': date.isoformat(),
                'text': text,
                'direction': 'incoming',
                'status': 'created'}
    return document


class SMSReceiver:

    @cherrypy.expose
    def index(self):
        return "SMS receiver working."

    @cherrypy.expose
    def new(self, identity=None, text=None):
        # we don't give a shit about empty or anonymous message
        if not identity or not text:
            return

        doc_id = database.create(document_from_sms(identity, \
                                                   text, date=datetime.now()))
        doc = database[doc_id]

        return doc


def main():
    cherrypy.quickstart(SMSReceiver(), \
                        '/', \
                        {'global': {'server.socket_port': KANOUCHD_PORT}})

if __name__ == '__main__':
    main()
