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
import json
from lavapdu.dbhandler import DBHandler
from lavapdu.shared import drivername_from_hostname


class ListenerServer(object):

    def __init__(self, config):
        self.config = config
        settings = config["daemon"]
        listen_host = settings["hostname"]
        listen_port = settings["port"]

        logging.getLogger().name = "ListenerServer"
        logging.getLogger().setLevel(settings["logging_level"])
        logging.debug("ListenerServer __init__")
        logging.info("listening on %s:%s", listen_host, listen_port)

        self.server = TCPServer((listen_host, listen_port), TCPRequestHandler)
        self.server.settings = settings
        self.server.config = config
        dbh = DBHandler(settings)
        dbh.create_db()
        dbh.close()
        del dbh

    def start(self):
        logging.info("Starting the ListenerServer")
        self.server.serve_forever()


class TCPRequestHandler(SocketServer.BaseRequestHandler):
    # "One instance per connection.  Override handle(self) to customize
    # action."
    def insert_request(self, data):
        logging.getLogger().name = "TCPRequestHandler"
        logging.getLogger().setLevel(self.server.settings["logging_level"])
        array = data.split(" ")
        delay = 10
        custom_delay = False
        now = int(time.time())
        if (len(array) < 3) or (len(array) > 4):
            logging.info("Wrong data size")
            raise Exception("Unexpected data")
        if len(array) == 4:
            delay = int(array[3])
            custom_delay = True
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        drivername_from_hostname(hostname, self.server.config["pdus"])
        if not (request in ["reboot", "on", "off"]):
            logging.info("Unknown request: %s", request)
            raise Exception("Unknown request: %s", request)
        if request == "reboot":
            logging.debug("reboot requested, submitting off/on")
            self.queue_request(hostname, port, "off", now)
            self.queue_request(hostname, port, "on", now + delay)
        else:
            if custom_delay:
                logging.debug("using delay as requested")
                self.queue_request(hostname, port, request, now + delay)
            else:
                self.queue_request(hostname, port, request, now)

    def queue_request(self, hostname, port, request, exectime):
        dbhandler = DBHandler(self.server.settings)
        sql = "insert into pdu_queue (hostname,port,request,exectime) " \
              "values ('%s',%i,'%s',%i)" % (hostname, port, request, exectime)
        dbhandler.do_sql(sql)
        dbhandler.close()
        del dbhandler

    def handle(self):
        logging.getLogger().name = "TCPRequestHandler"
        request_ip = self.client_address[0]
        try:
            data = self.request.recv(4096).strip()
            socket.setdefaulttimeout(2)
            try:
                request_host = socket.gethostbyaddr(request_ip)[0]
            except socket.herror:
                request_host = request_ip
            logging.info("Received a request from %s: '%s'",
                         request_host,
                         data)
            self.insert_request(data)
            self.request.sendall("ack\n")
        except Exception as global_error:  # pylint: disable=broad-except
            logging.debug(global_error.__class__)
            logging.debug(global_error.message)
            self.request.sendall(global_error.message)
        self.request.close()


class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Executing from __main__")
    filename = "/etc/lavapdu/lavapdu.conf"
    logging.debug("Reading settings from %s", filename)
    with open(filename) as stream:
        jobdata = stream.read()
        json_data = json.loads(jobdata)
    ss = ListenerServer(json_data)
    ss.start()
