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
import psycopg2
import logging
import socket


class DBHandler(object):
    def __init__(self, config):
        logging.debug("Creating new DBHandler: %s" % config["dbhost"])
        logging.getLogger().name = "DBHandler"
        self.conn = psycopg2.connect(database=config["dbname"], user=config["dbuser"],
                                     password=config["dbpass"], host=config["dbhost"])
        self.cursor = self.conn.cursor()

    def do_sql(self, sql):
        logging.debug("executing sql: %s" % sql)
        self.cursor.execute(sql)
        self.conn.commit()

    def do_sql_with_fetch(self, sql):
        logging.debug("executing sql: %s" % sql)
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        self.conn.commit()
        return row

    def delete_row(self, row_id):
        logging.debug("deleting row %i" % row_id)
        self.do_sql("delete from pdu_queue where id=%i" % row_id)

    def get_res(self, sql):
        return self.cursor.execute(sql)

    def get_next_job(self):
        row = self.do_sql_with_fetch("select * from pdu_queue order by id asc limit 1")
        return row

    def close(self):
        logging.debug("Closing DBHandler")
        self.cursor.close()
        self.conn.close()


class ListenerServer(object):

    def __init__(self, config):
        self.server = TCPServer((config["hostname"], config["port"]), TCPRequestHandler)
        logging.getLogger().name = "ListenerServer"
        logging.getLogger().setLevel(config["logging_level"])
        logging.info("listening on %s:%s" % (config["hostname"], config["port"]))
        self.server.config = config
        self.db = DBHandler(config)
        self.create_db()
        self.db.close()
        del(self.db)

    def create_db(self):
        sql = "create table if not exists pdu_queue (id serial, hostname text, port int, request text)"
        self.db.do_sql(sql)

    def start(self):
        logging.info("Starting the ListenerServer")
        self.server.serve_forever()


class TCPRequestHandler(SocketServer.BaseRequestHandler):
    #"One instance per connection.  Override handle(self) to customize action."
    def insert_request(self, data):
        logging.getLogger().name = "TCPRequestHandler"
        array = data.split(" ")
        if len(array) != 3:
            logging.info("Wrong data size")
            raise Exception("Unexpected data")
        hostname = array[0]
        port = int(array[1])
        request = array[2]
        if not (request in ["reboot", "on", "off", "delayed"]):
            logging.info("Unknown request: %s" % request)
            raise Exception("Unknown request: %s" % request)
        db = DBHandler(self.server.config)
        sql = "insert into pdu_queue (hostname,port,request) values ('%s',%i,'%s')" % (hostname, port, request)
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
                logging.debug("Unable to resolve: %s error: %s" % (ip, e))
                request_host = ip
            logging.info("Received a request from %s: '%s'" % (request_host, data))
            self.insert_request(data)
            self.request.sendall("ack\n")
        except Exception as e:
            logging.debug(e)
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
               "port": 16421,
               "dbhost": "127.0.0.1",
               "dbuser": "pdudaemon",
               "dbpass": "pdudaemon",
               "dbname": "lavapdu",
               "logging_level": logging.DEBUG}
    ss = ListenerServer(starter)
    ss.start()
