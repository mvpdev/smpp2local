#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

''' webserver expecting identity and text to store incoming sms in CouchDB '''

import sys
from datetime import datetime
import logging as log

import cherrypy
import couchdb

from config import *

log.basicConfig(level=log.INFO, filename=KANOUCHD_LOG_FILE)


def document_from_sms(identity, text, date=datetime.now()):
    ''' returns dictionary matching CouchDB and RSMS backend format '''
    document = {'identity': identity,
                'datetime': date.isoformat(),
                'text': text,
                'direction': 'incoming',
                'status': 'created'}
    return document


def save_document_to_couch(document):
    ''' saves an arbitrary document to CouchDB '''

    # connect DB upon message reception.
    # this is not very good for performance
    # but it allows CouchDB restarts without effects.
    couch = couchdb.Server(COUCH_SERVER)
    database = couch[COUCH_DB]

    # create a Couch document and save it to DB.
    doc_id, doc_rev = database.save(document)
    doc = database[doc_id]
    return doc_id


class SMSReceiver:

    @cherrypy.expose
    def index(self):
        return "SMS receiver working."

    @cherrypy.expose
    def new(self, identity=None, text=None):
        # we don't give a shit about empty or anonymous message
        if not identity or not text:
            return

        document = document_from_sms(identity, text, date=datetime.now())

        try:
            doc = save_document_to_couch(document)
        except:
            # I believe this should prevent kannel from discarding the
            # incoming sms and add it to retry spool.
            log.critical("can't connect or create document on CouchDB.")
            raise cherrypy.HTTPError(500, u"Server could not create message" \
                                           " into CouchDB.")

        return doc


def main():
    cherrypy.quickstart(SMSReceiver(), \
                        '/', \
                        {'global': {'server.socket_port': KANOUCHD_PORT}})

if __name__ == '__main__':
    try:
        log.info("started.")
        main()
        log.info("soft shutdown.")
        shutdown()
    except KeyboardInterrupt:
        log.warning("shutdown with ^C.")
        shutdown()
    except Exception, e:
        log.error("shutdown by exception: %r" % e)
        shutdown()
