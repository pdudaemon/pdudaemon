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
log = logging.getLogger(__name__)


class DBHandler(object):
    def __init__(self, config):
        log.debug("Creating new DBHandler: %s %s", config["dbhost"],
                  config["dbname"])
        self.config = config
        self.open_connection()

    def open_connection(self):
        retry = self.config.get("dbretry", 10)
        while retry >= 0:
            try:
                log.debug("Opening DB connection")
                self.conn = psycopg2.connect(database=self.config["dbname"],
                                             user=self.config["dbuser"],
                                             password=self.config["dbpass"],
                                             host=self.config["dbhost"])
                self.cursor = self.conn.cursor()
                break
            except Exception as e:
                log.debug("DB connection opening failed: %s" % repr(e))
                log.debug("Retrying for %s more time" % retry)
                retry -= 1
                time.sleep(self.config.get("dbretryinterval", 60))

    def do_sql(self, sql):
        log.debug("executing sql: %s", sql)
        try:
            self.cursor.execute(sql)
            self.conn.commit()
        except:
            self.close()
            self.open_connection()
            self.cursor.execute(sql)
            self.conn.commit()

    def do_sql_with_fetch(self, sql):
        log.debug("executing sql: %s", sql)
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.conn.commit()
            return row
        except:
            self.close()
            self.open_connection()
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.conn.commit()
            return row

    def create_db(self):
        log.info("Creating db table if it doesn't exist")
        sql = "create table if not exists pdu_queue (id serial, hostname " \
              "text, port int, request text, exectime int)"
        self.do_sql(sql)
        sql = "select column_name from information_schema.columns where " \
              "table_name='pdu_queue' and column_name='exectime'"
        res = self.do_sql_with_fetch(sql)
        if not res:
            log.info("Old db schema discovered, upgrading")
            sql = "alter table pdu_queue add column exectime int default 1"
            self.do_sql(sql)

    def insert_request(self, hostname, port, request, exectime):
        sql = "insert into pdu_queue (hostname,port,request,exectime) " \
              "values ('%s',%i,'%s',%i)" % (hostname, port, request, exectime)
        self.do_sql(sql)

    def delete_row(self, row_id):
        log.debug("deleting row %i", row_id)
        self.do_sql("delete from pdu_queue where id=%i" % row_id)

    def get_res(self, sql):
        return self.cursor.execute(sql)

    def purge(self):
        log.debug("Purging all jobs from database")
        self.do_sql("delete from pdu_queue")
        self.close()

    def get_next_job(self, single_pdu=False):
        now = int(time.time())
        extra_sql = ""
        if single_pdu:
            log.debug("Looking for jobs for PDU: %s", single_pdu)
            extra_sql = "and hostname='%s'" % single_pdu
        row = self.do_sql_with_fetch("select id, hostname, port, request "
                                     "from pdu_queue where ((exectime < %i "
                                     "or exectime is null) %s) order by id asc"
                                     " limit 1" % (now, extra_sql))
        return row

    def close(self):
        log.debug("Closing DBHandler")
        try:
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            log.warning("Failed to close DBHandler: %s" % repr(e))
