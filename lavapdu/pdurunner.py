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
from dbhandler import DBHandler
import traceback

class PDURunner():

    def __init__(self, config):
        logging.basicConfig(level=config["logging_level"])
        logging.getLogger().setLevel(config["logging_level"])
        logging.getLogger().name = "PDURunner"
        self.config = config
        self.pdus = config["pdus"]

    def get_one(self, db):
        job = db.get_next_job()
        if job:
            job_id, hostname, port, request = job
            logging.debug(job)
            logging.info("Processing queue item: (%s %s) on hostname: %s" % (request, port, hostname))
            res = self.do_job(hostname, port, request)
            db.delete_row(job_id)
        else:
            logging.debug("Found nothing to do in database")

    def driver_from_hostname(self, hostname):
        logging.debug("Trying to find a driver for %s" % hostname)
        logging.debug(self.pdus)
        driver = self.pdus[hostname]["driver"]
        logging.debug("Driver: %s" % driver)
        module = __import__("drivers.%s" % driver.lower(), fromlist=[driver])
        class_ = getattr(module, driver)
        return class_(hostname)

    def do_job(self, hostname, port, request, delay=0):
        retries = 10
        while retries > 0:
            try:
                driver = self.driver_from_hostname(hostname)
                return driver.handle(request, port, delay)
            except Exception as e:
                driver.cleanup()
                logging.warn(traceback.format_exc())
                logging.warn("Failed to execute job: %s %s %s (attempts left %i) error was %s" %
                             (hostname, port, request, retries, e.message))
                time.sleep(5)
                retries -= 1
        return False

    def run_me(self):
        logging.info("Starting up the PDURunner")
        while 1:
            db = DBHandler(self.config["settings"])
            self.get_one(db)
            db.close()
            del(db)
            time.sleep(2)

if __name__ == "__main__":
    starter = { "settings": {"dbhost": "127.0.0.1",
               "dbuser": "pdudaemon",
               "dbpass": "pdudaemon",
               "dbname": "lavapdu"},
                "pdus": { "pdu14": { "driver": "APC9218" },"pdu15": {"driver": "APC8959"} },
               "logging_level": logging.DEBUG}
    p = PDURunner(starter)
    p.do_job("pdu15",18,"off",10)
    p.do_job("pdu15",18,"reboot",10)
    p.do_job("pdu15",18,"on",10)
    #p.run_me()
