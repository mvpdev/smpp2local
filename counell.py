#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

''' sends HTTP requests to a kannel server

1. Retrieves the list of messages from CouchDB
2. Sends them all, one by one to Kannel
3. exits

this script is meant to be fired at any time to process the pool of
pending outgoing messages.
a typical use is to set it as couchdb notification client. '''

import os
import re
import time
import sys
import fcntl
import urllib
import httplib
import logging as log


import couchdb

from config import *

# global variables holding CouchDB connection and logger
try:
    couch = couchdb.Server(COUCH_SERVER)
except:
    die("CouchDB is not started.")
database = couch[COUCH_DB]

try:
    COUCH_PID = int(open(COUCH_PID_FILE, 'r').read().strip())
except:
    die("can't retrieve CouchDB PID.")
log.basicConfig(level=log.INFO, filename=COUNELL_LOG_FILE)


def couch_is_running():
    # send 
    try:
        os.kill(COUCH_PID, 0)
    except OSError:
        print "OSERROR"
        return False
    else:
        return True


def get_messages_from_couch():
    ''' fecthes all pending outgoing messages in couch and return them '''
    messages = []

    # uses permanent view if defined
    # use a temporary view if not.
    if COUCH_KANNEL_VIEW:
        results = database.view(COUCH_KANNEL_VIEW)
    else:
        map_fun = '''function(doc) {
            if (doc.direction == 'outgoing' && doc.status == 'created')
                emit(doc, null);
            }'''
        results = database.query(map_fun)
    for row in results:
        messages.append(row.key)

    return messages


def send_message_to_kannel(message):
    ''' send an individual message (couch dict) to kannel

    if sending is successful, changes its flag in Couch '''

    # need to convert message to encode it
    # for URL. Couch is always utf-8.
    # we keep utf-8 and inform kannel of that (&charset)
    message_text = message['text']
    message_text = message_text.encode('utf-8')
    message_text = urllib.quote(message_text)

    # removes non-number char from identity.
    # alpha are not illegal but it's not likely we'll
    # need that and probably blocks some user errors.
    message_identity = message['identity'].strip()
    re.compile('\D').sub('', message_identity)

    success, retcode = http_request(KANNEL_SERVER_STRING, KANNEL_PATH \
                                    % {'identity': \
                                               message_identity, \
                                       'text': message_text})

    if success:
        log.info("kannel accepted message %s." % message['_id'])
        # message sent successfuly.
        # mark it as done in Couch
        doc = database[message['_id']]
        doc.update({'status': 'processed'})
        database.update([doc])
        log.info("couch updated message %s." % message['_id'])
    else:
        # message has NOT been processed nor stored by kannel
        # we will need to retry it later.
        log.warning("kannel failed to send %s and returned: %s." \
                     % (message, retcode))


def http_request(server, path):
    ''' process a GET request to server/path and return acceptance '''
    conn = httplib.HTTPConnection(server)
    conn.request("GET", path.replace(' ', '+'))
    ret = conn.getresponse()
    return (ret.status == 202, ret.status)


def send_messages_to_kannel(messages):
    ''' wrapper around individual message sending

    allows manipulation of pending messages (exclude previous erroneous? '''
    for message in messages:
        log.info("sending message %s to kannel." % message['_id'])
        send_message_to_kannel(message)


def main():

    # make stdin a non-blocking file
    # so that we don't waste CPU waiting.
    fd = sys.stdin.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    # set a timer so that after X iterations (1s each)
    # we can check if CouchDB is still there
    # as CouchDB doesn't kill our process when it restarts.
    timer = 0

    # looping forever
    # triggers kannel connection once something comes on stdin.
    while sys.stdin:
        timer += 1
        if timer >= COUCH_CHECK_INTERVAL:
            if not couch_is_running():
                die("CouchDB died. commiting suicide.")
        try:
            data = sys.stdin.readline()
        except:
            continue
        log.info("received data from CouchDB: %s" % data)
        if data:
            messages = get_messages_from_couch()
            log.info("%d message(s) from CouchDB" % messages.__len__())
            send_messages_to_kannel(messages)
        else:
            time.sleep(1)


def shutdown(status=0):
    log.shutdown()
    exit(status)


def die(message=None):
    if message:
        log.critical(message)
    shutdown(1)


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
