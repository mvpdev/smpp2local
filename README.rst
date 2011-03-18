Setup Remote Server
===================


Install CouchDB
~~~~~~~~~~~~~~~

* Edit /etc/couchdb/local.ini

| port = 5900
| bind_address = 0.0.0.0
| secret = xxxx
| [update_notification]
| ccsms=/var/lib/couchdb/smpp2local/counell.py

* Restart CouchDB (comment with ; the last line until rest of config is done)

Create messages DB
~~~~~~~~~~~~~~~~~~

Use "Create Database" link on http://REMOTE:5900/_utils to add ``cc_sms`` DB.

Install SMPP2Local
~~~~~~~~~~~~~~~~~~
* ``aptitude install python-couchdb python-cherrypy``

* ``git clone git://github.com/mvpdev/smpp2local.git smpp2local``

* Edit ``local_config.py`` and override server config.

Install cleanup script
~~~~~~~~~~~~~~~~~~~~~~

``ln -s /var/lib/couchdb/smpp2local/cleanup_obsolete.py /etc/cron.daily/``

Setup Local Server
==================

Install CouchDB
~~~~~~~~~~~~~~~

* Edit /etc/couchdb/local.ini

| port = 5900
| bind_address = 127.0.0.1

* Restart CouchDB

Create messages DB
~~~~~~~~~~~~~~~~~~

Use "Create Database" link on http://localhost:5900/_utils to add ``cc_sms`` DB.

Setup Replication
~~~~~~~~~~~~~~~~~

    ``curl -X POST http://localhost:5900/_replicate -d '{"source":"http://REMOTE:5900/cc_sms", "target":"cc_sms", "continuous":true}'``

    ``curl -X POST http://localhost:5900/_replicate -d '{"source":"cc_sms", "target":"http://REMOTE:5900/cc_sms", "continuous":true}'``

WARNING: continuous replication is not stored after CouchDB restart on CouchDB 0.10.

Create test documents and check that you can see both on both servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ``curl -X PUT http://localhost:5900/cc_sms/bloup -d '{"title":"Hello, I am from the ground"}'``

    ``curl -X PUT http://REMOTE:5900/cc_sms/bloup -d '{"title":"Do not panic, I am from the Internet"}'``

Create Permanent Views
======================

Using the "Temporary View" link on http://localhost:5900/_utils, create two different views and save them as permanent:

* cc/kannel

| function(doc) {
|   if (doc.direction == 'outgoing' && doc.status == 'created') {
|     emit(doc, null);
|   }
| }

* cc/rapidsms

| function(doc) {
|   if (doc.direction == 'incoming' && doc.status == 'created') {
|     emit(doc, null);
|   }
| }

* cc/processed

| function(doc) {
|   if (doc.direction && doc.status == 'processed') {
|     emit(doc, null);
|   }
| }

Reproduce on the remote server.
