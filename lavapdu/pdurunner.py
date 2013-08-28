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
import time
from engine import PDUEngine
from socketserver import DBHandler

class PDURunner():

    def __init__(self, config):
        logging.basicConfig(level=config["logging_level"])
        logging.getLogger().setLevel(config["logging_level"])
        logging.getLogger().name = "PDURunner"
        self.config = config

    def get_one(self, db):
        job = db.get_next_job()
        if job:
            job_id,hostname,port,request = job
            logging.info("Processing queue item: (%s %s) on hostname: %s" % (request, port, hostname))
            #logging.debug(id, hostname, request, port)
            res = self.do_job(hostname,port,request)
            db.delete_row(job_id)
        else:
            logging.debug("Found nothing to do in database")

    def do_job(self, hostname, port, request):
        retries = 5
        while retries > 0:
            try:
                pe = PDUEngine(hostname, 23)
                if request == "reboot":
                    pe.driver.port_reboot(port)
                elif request == "on":
                    pe.driver.port_on(port)
                elif request == "off":
                    pe.driver.port_off(port)
                elif request == "delayed":
                    pe.driver.port_delayed(port)
                else:
                    logging.debug("Unknown request type: %s" % request)
                pe.pduclose()
                retries = 0
            except:
                logging.warn("Failed to execute job: %s %s %s (attempts left %i)" % (hostname,port,request,retries))
                #logging.warn(e)
                time.sleep(5)
                retries -= 1


    def run_me(self):
        logging.info("Starting up the PDURunner")
        while 1:
            db = DBHandler(self.config)
            self.get_one(db)
            db.close()
            del(db)
            time.sleep(2)

if __name__ == "__main__":
    starter = {"dbhost":"127.0.0.1",
               "dbuser":"pdudaemon",
               "dbpass":"pdudaemon",
               "dbname":"lavapdu",
               "logging_level": logging.DEBUG}
    p = PDURunner(starter)
    p.run_me()