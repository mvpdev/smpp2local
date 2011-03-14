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

import urllib
import httplib

import couchdb

from config import *

couch = couchdb.Server(COUCH_SERVER)
database = couch[COUCH_DB]


def get_messages_from_couch():
    ''' fecthes all pending outgoing messages in couch and return them '''
    messages = []

    map_fun = '''function(doc) {
        if (doc.direction == 'outgoing' && doc.status == 'created')
            emit(doc, null);
        }'''
    for row in database.query(map_fun):
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
        # message sent successfuly.
        # mark it as done in Couch
        doc = database[message['_id']]
        doc.update({'status': 'processed'})
        database.update([doc])
    else:
        # message has NOT been processed nor stored by kannel
        # we will need to retry it later.
        print "KANNEL FAILED TO SEND %s and returned: %s" % (message, retcode)


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
        print "PROCESSING: %s" % message
        send_message_to_kannel(message)


def main():
    messages = get_messages_from_couch()
    send_messages_to_kannel(messages)

if __name__ == '__main__':
    main()
