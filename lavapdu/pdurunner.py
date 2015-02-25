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
import json
import traceback
from lavapdu.dbhandler import DBHandler
from lavapdu.drivers.driver import PDUDriver
import lavapdu.drivers.strategies

class PDURunner(object):

    def __init__(self, config):
        self.pdus = config["pdus"]
        self.settings = config["daemon"]
        logging.basicConfig(level=self.settings["logging_level"])
        logging.getLogger().setLevel(self.settings["logging_level"])
        logging.getLogger().name = "PDURunner"

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
        logging.debug("Trying to find a driver for hostname %s" % hostname)
        logging.debug(self.pdus)
        if hostname in self.pdus:
            drivername = (self.pdus[hostname]["driver"])
        else:
            raise NotImplementedError("No configuration available for hostname %s\n"
                                      "Is there a section in the lavapdu.conf?" % hostname)
        logging.debug("Config file wants driver: %s" % drivername)
        driver = PDUDriver.select(drivername)(hostname, self.pdus[hostname])
        return driver

    def do_job(self, hostname, port, request, delay=0):
        retries = self.settings["retries"]
        driver = False
        while retries > 0:
            try:
                driver = self.driver_from_hostname(hostname)
                return driver.handle(request, port, delay)
            except Exception as e:
                logging.warn(traceback.format_exc())
                logging.warn("Failed to execute job: %s %s %s (attempts left %i) error was %s" %
                             (hostname, port, request, retries, e.message))
                if driver:
                    #driver._cleanup()
                    driver._bombout()
                time.sleep(5)
                retries -= 1
        return False

    def run_me(self):
        logging.info("Starting up the PDURunner")
        while 1:
            db = DBHandler(self.settings)
            self.get_one(db)
            db.close()
            del(db)
            time.sleep(2)

if __name__ == "__main__":
    settings = {}
    filename = "/etc/lavapdu/lavapdu.conf"
    print("Reading settings from %s" % filename)
    with open(filename) as stream:
        jobdata = stream.read()
        json_data = json.loads(jobdata)

    p = PDURunner(json_data)
    #p.do_job("192.168.10.5",18,"reboot",2)
    p.run_me()
