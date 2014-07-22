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
from dbhandler import DBHandler


class ListenerServer(object):

    def __init__(self, config):
        self.server = TCPServer((config["settings"]["hostname"], config["settings"]["port"]), TCPRequestHandler)
        logging.getLogger().name = "ListenerServer"
        logging.getLogger().setLevel(config["logging_level"])
        logging.info("listening on %s:%s" % (config["settings"]["hostname"], config["settings"]["port"]))
        self.server.settings = config["settings"]
        self.db = DBHandler(self.server.settings)
        self.create_db()
        self.db.close()
        del(self.db)

    def create_db(self):
        sql = "create table if not exists pdu_queue (id serial, hostname text, port int, request text, exectime int)"
        self.db.do_sql(sql)
        sql = "select column_name from information_schema.columns where table_name='pdu_queue'" \
              "and column_name='exectime'"
        res = self.db.do_sql_with_fetch(sql)
        if not res:
            logging.info("Old db schema discovered, upgrading")
            sql = "alter table pdu_queue add column exectime int default 1"
            self.db.do_sql(sql)

    def start(self):
        logging.info("Starting the ListenerServer")
        self.server.serve_forever()


class TCPRequestHandler(SocketServer.BaseRequestHandler):
    #"One instance per connection.  Override handle(self) to customize action."
    def insert_request(self, data):
        logging.getLogger().name = "TCPRequestHandler"
        array = data.split(" ")
        delay = 10
        custom_delay = False
        now = int(time.time())
        if len(array) < 3:
            logging.info("Wrong data size")
            raise Exception("Unexpected data")
        if len(array) == 4:
            delay = int(array[3])
            custom_delay = True
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        if not (request in ["reboot","on","off"]):
            logging.info("Unknown request: %s" % request)
            raise Exception("Unknown request: %s" % request)
        if request == "reboot":
            logging.debug("reboot requested, submitting off/on")
            self.queue_request(hostname,port,"off",now)
            self.queue_request(hostname,port,"on",now+delay)
        else:
            if custom_delay:
                logging.debug("using delay as requested")
                self.queue_request(hostname,port,request,now+delay)
            else:
                self.queue_request(hostname,port,request,now)

    def queue_request(self, hostname, port, request, exectime):
        db = DBHandler(self.server.settings)
        sql = "insert into pdu_queue (hostname,port,request,exectime)" \
              "values ('%s',%i,'%s',%i)" % (hostname,port,request,exectime)
        db.do_sql(sql)
        db.close()
        del(db)


    def handle(self):
        logging.getLogger().name = "TCPRequestHandler"
        ip = self.client_address[0]
        try:
            data = self.request.recv(4096).strip()
            socket.setdefaulttimeout(2)
            try:
                request_host = socket.gethostbyaddr(ip)[0]
            except socket.herror as e:
                logging.debug("Unable to resolve: %s error: %s" % (ip,e))
                request_host = ip
            logging.info("Received a request from %s: '%s'" % (request_host, data))
            self.insert_request(data)
            self.request.sendall("ack\n")
        except Exception as e:
            logging.debug(e.__class__)
            logging.debug(e.message)
            self.request.sendall("nack\n")
        self.request.close()

class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Executing from __main__")
    starter = {"hostname": "0.0.0.0",
               "port":16421,
               "dbhost":"127.0.0.1",
               "dbuser":"pdudaemon",
               "dbpass":"pdudaemon",
               "dbname":"lavapdu",
               "logging_level": logging.DEBUG}
    ss = ListenerServer(starter)
    ss.start()