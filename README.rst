
Install CouchDB on Kannel server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Edit /etc/couchdb/local.ini

* port = 5900

* bind_address = 0.0.0.0

* secret = xxxx

| [update_notification]
| ccsms=/usr/local/smpp2local/counell.py

Create cc_sms DB
~~~~~~~~~~~~~~~~

Install CouchDB on local server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Edit /etc/couchdb/local.ini

** port = 5900

** bind_address = 127.0.0.1

Create cc_sms DB
~~~~~~~~~~~~~~~~

setup replication (on the local server):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
curl -X POST http://localhost:5900/_replicate -d '{"source":"http://REMOTE:5900/cc_sms", "target":"cc_sms", "continuous":true}'

curl -X POST http://localhost:5900/_replicate -d '{"source":"cc_sms", "target":"http://REMOTE:5900/cc_sms", "continuous":true}'

Create test documents and check that you can see both on both servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
curl -X PUT http://localhost:5900/cc_sms/bloup -d '{"title":"Hello, I am from the ground"}'

curl -X PUT http://REMOTE:5900/cc_sms/bloup -d '{"title":"Do not panic, I am from the Internet"}'

Install SMPP2Local on Kannel Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ``aptitude install python-couchdb python-cherrypy``

    ``git clone git://github.com/mvpdev/smpp2local.git smpp2local``

    Edit ``local_config.py`` and reflect server config.
