#! /usr/bin/python

#  Copyright 2018 Matt Hart <matt@mattface.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    import urlparse
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import urllib.parse as urlparse
import logging
import time
import sys
import os
from pdudaemon.dbhandler import DBHandler
from pdudaemon.shared import drivername_from_hostname
log = logging.getLogger(__name__)


class PDUHTTPHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        log.info("Handling HTTP request from %s: %s" % (self.client_address, self.path))
        data = urlparse.parse_qs(urlparse.urlparse(self.path).query)
        path = urlparse.urlparse(self.path).path
        res = self.insert_request(data, path)
        if res:
            self._set_headers(200)
            self.wfile.write("OK - accepted request\n".encode('utf-8'))
        else:
            self._set_headers(500)
            self.wfile.write("Invalid request\n".encode('utf-8'))

    def insert_request(self, data, path):
        delay = 5
        entry = path.lstrip('/').split('/')
        if len(entry) != 3:
            log.info("Request path was invalid: %s" % entry)
            return False
        if not (entry[0] == 'power' and entry[1] == 'control'):
            log.info("Unknown request, path was %s" % path)
            return False
        request = entry[2]
        custom_delay = False
        now = int(time.time())
        if data.get('delay', None):
            delay = data.get('delay')[0]
            custom_delay = True
        hostname = data.get('hostname', [None])[0]
        port = data.get('port', [None])[0]
        if not hostname or not port or not request:
            log.info("One of hostname,port,request was not set")
            return False
        drivername_from_hostname(hostname, self.server.config["pdus"])
        dbh = self.server.dbh
        if not (request in ["reboot", "on", "off"]):
            log.info("Unknown request: %s", request)
            return False
        if request == "reboot":
            log.debug("reboot requested, submitting off/on")
            dbh.insert_request(hostname, port, "off", now)
            dbh.insert_request(hostname, port, "on", now + int(delay))
            return True
        else:
            if custom_delay:
                log.debug("using delay as requested")
                dbh.insert_request(hostname, port, request, now + delay)
                return True
            else:
                dbh.insert_request(hostname, port, request, now)
                return True


class PDUHTTPListener(object):

    def __init__(self, config):
        self.config = config
        settings = config["daemon"]
        listen_host = settings["hostname"]
        listen_port = settings.get("port", 16421)
        log.debug("PDUHTTPListener __init__")
        log.info("listening on %s:%s", listen_host, listen_port)

        self.server = HTTPServer((listen_host, listen_port), PDUHTTPHandler)
        self.server.settings = settings
        self.server.config = config
        self.server.dbh = DBHandler(settings)
        self.server.dbh.create_db()

    def start(self):
        log.info("Starting the HTTP server")
        self.server.serve_forever()
