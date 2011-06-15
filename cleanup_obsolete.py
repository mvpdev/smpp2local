#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

''' removes CouchDB messages older than specified delta

    This script is supposed to be run nightly. '''

import re
import datetime

import couchdb

from config import *

# global variables holding CouchDB connection and logger
log.basicConfig(level=log.INFO, filename=CLEANUP_LOG_FILE)

try:
    couch = couchdb.Server(COUCH_SERVER)
    database = couch[COUCH_DB]
except IndexError:
    die("database %s doesn't exist in CouchDB" % COUCH_DB)
except:
    die("CouchDB is not started.")


def get_messages_from_couch():
    ''' fecthes all processed messages in couch and return them '''
    messages = []
    delta = datetime.timedelta(CLEANUP_TIMEDELTA)
    today = datetime.datetime.now()

    # uses permanent view if defined
    # use a temporary view if not.
    if COUCH_PROCESSED_VIEW:
        results = database.view(COUCH_PROCESSED_VIEW)
    else:
        map_fun = '''function(doc) {
            if (doc.direction && doc.status == 'processed')
                emit(doc, null);
            }'''
        results = database.query(map_fun)
    for row in results:
        message = row.key
        try:
            date = datetime.datetime(*map(int, re.split('[^\d]', \
                                          message['datetime'])[:-1]))
        except:
            # if it has no datetime, it's not
            # for us anyway.
            continue

        if (today - delta) > date:
            messages.append(message)

    return messages


def delete_document_from_couch(document_id):
    doc = database[document_id]
    database.delete(doc)


def main():
    messages = get_messages_from_couch()
    log.info("%d messages to delete from CouchDB" % messages.__len__())
    for message in messages:
        log.info("Deleting message %s" % message['_id'])
        try:
            delete_document_from_couch(message['_id'])
        except Exception as e:
            log.error("failed to delete %s from CouchDB. %r" \
                      % (message['_id'], e))


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
