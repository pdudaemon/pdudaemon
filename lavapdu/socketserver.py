#! /usr/bin/python

#  Copyright 2013 Linaro Limited
#  Author Matt Hart <matthew.hart@linaro.org>
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

import SocketServer
import logging
import socket
import time
import sys
import os
from lavapdu.dbhandler import DBHandler
from lavapdu.shared import drivername_from_hostname
log = logging.getLogger(__name__)


class ListenerServer(object):

    def __init__(self, config):
        self.config = config
        settings = config["daemon"]
        listen_host = settings["hostname"]
        listen_port = settings["port"]
        log.debug("ListenerServer __init__")
        if "purge" in config:
            self.server.dbh.purge()
            sys.exit(os.EX_OK)
        log.info("listening on %s:%s", listen_host, listen_port)

        self.server = TCPServer((listen_host, listen_port), TCPRequestHandler)
        self.server.settings = settings
        self.server.config = config
        self.server.dbh = DBHandler(settings)

    def start(self):
        log.info("Starting the ListenerServer")
        self.server.serve_forever()


class TCPRequestHandler(SocketServer.BaseRequestHandler):
    # "One instance per connection.  Override handle(self) to customize
    # action."
    def insert_request(self, data):
        array = data.split(" ")
        delay = 10
        custom_delay = False
        now = int(time.time())
        if (len(array) < 3) or (len(array) > 4):
            log.info("Wrong data size")
            raise Exception("Unexpected data")
        if len(array) == 4:
            delay = int(array[3])
            custom_delay = True
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        # this will throw if the pdu is not found
        drivername_from_hostname(hostname, self.server.config["pdus"])
        dbh = self.server.dbh
        if not (request in ["reboot", "on", "off"]):
            log.info("Unknown request: %s", request)
            raise Exception("Unknown request: %s", request)
        if request == "reboot":
            log.debug("reboot requested, submitting off/on")
            dbh.insert_request(hostname, port, "off", now)
            dbh.insert_request(hostname, port, "on", now + delay)
        else:
            if custom_delay:
                log.debug("using delay as requested")
                dbh.insert_request(hostname, port, request, now + delay)
            else:
                dbh.insert_request(hostname, port, request, now)

    def handle(self):
        request_ip = self.client_address[0]
        try:
            data = self.request.recv(4096).strip()
            socket.setdefaulttimeout(2)
            try:
                request_host = socket.gethostbyaddr(request_ip)[0]
            except socket.herror:
                request_host = request_ip
            log.info("Received a request from %s: '%s'",
                     request_host,
                     data)
            self.insert_request(data)
            self.request.sendall("ack\n")
        except Exception as global_error:  # pylint: disable=broad-except
            log.debug(global_error.__class__)
            log.debug(global_error.message)
            self.request.sendall(global_error.message)
        self.request.close()


class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
