#!/usr/bin/python3

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

import socketserver
import threading
import logging
import socket
import time
logger = logging.getLogger('pdud.tcp')


class TCPListener(threading.Thread):

    def __init__(self, config, db_queue):
        super(TCPListener, self).__init__(name="TCP Listener")
        settings = config["daemon"]
        listen_host = settings["hostname"]
        listen_port = settings.get("port", 16421)
        logger.info("listening on %s:%s", listen_host, listen_port)
        self.server = TCPServer((listen_host, listen_port), TCPRequestHandler)
        self.server.settings = settings
        self.server.config = config
        self.server.db_queue = db_queue

    def run(self):
        logger.info("Starting the TCPServer")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()


class TCPRequestHandler(socketserver.BaseRequestHandler):
    def insert_request(self, data):
        array = data.split(" ")
        delay = 10
        custom_delay = False
        now = int(time.time())
        if (len(array) < 3) or (len(array) > 4):
            logger.info("Wrong data size")
            raise Exception("Unexpected data")
        if len(array) == 4:
            delay = int(array[3])
            custom_delay = True
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        db_queue = self.server.db_queue
        if not (request in ["reboot", "on", "off"]):
            logger.info("Unknown request: %s", request)
            raise Exception("Unknown request: %s", request)
        if request == "reboot":
            logger.debug("reboot requested, submitting off/on")
            db_queue.put(("CREATE", hostname, port, "off", now))
            db_queue.put(("CREATE", hostname, port, "on", now + int(delay)))
        else:
            if custom_delay:
                logger.debug("using delay as requested")
                db_queue.put(("CREATE", hostname, port, request, now + int(delay)))
            else:
                db_queue.put(("CREATE", hostname, port, request, now))

    def handle(self):
        request_ip = self.client_address[0]
        try:
            data = self.request.recv(16384)
            data = data.decode('utf-8')
            data = data.strip()
            socket.setdefaulttimeout(2)
            try:
                request_host = socket.gethostbyaddr(request_ip)[0]
            except socket.herror:
                request_host = request_ip
            logger.info("Received a request from %s: '%s'", request_host, data)
            self.insert_request(data)
            self.request.sendall("ack\n".encode('utf-8'))
        except Exception as global_error:  # pylint: disable=broad-except
            logger.debug(global_error.__class__)
            logger.debug(global_error)
            self.request.sendall(global_error)
        self.request.close()


class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
