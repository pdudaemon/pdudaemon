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

import logging
import psycopg2
import time

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

    def create_db(self):
        logging.info("Creating db table if it doesn't exist")
        sql = "create table if not exists pdu_queue (id serial, hostname " \
              "text, port int, request text, exectime int)"
        self.cursor.execute(sql)
        self.conn.commit()
        sql = "select column_name from information_schema.columns where " \
              "table_name='pdu_queue' and column_name='exectime'"
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        if not res:
            logging.info("Old db schema discovered, upgrading")
            sql = "alter table pdu_queue add column exectime int default 1"
            self.cursor.execute(sql)
        self.conn.commit()

    def delete_row(self, row_id):
        logging.debug("deleting row %i" % row_id)
        self.do_sql("delete from pdu_queue where id=%i" % row_id)

    def get_res(self, sql):
        return self.cursor.execute(sql)

    def get_next_job(self):
        now = int(time.time())
        row = self.do_sql_with_fetch("select id,hostname,port,request from pdu_queue where (exectime < %i or exectime is null) order by id asc limit 1" % now)
        return row

    def close(self):
        logging.debug("Closing DBHandler")
        self.cursor.close()
        self.conn.close()