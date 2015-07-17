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
import traceback
from lavapdu.dbhandler import DBHandler
from lavapdu.drivers.driver import PDUDriver
import lavapdu.drivers.strategies  # pylint: disable=W0611
from lavapdu.shared import drivername_from_hostname
from lavapdu.shared import pdus_from_config
assert lavapdu.drivers.strategies
log = logging.getLogger(__name__)


class PDURunner(object):

    def __init__(self, config, single_pdu=False):
        self.settings = config["daemon"]
        self.pdus = config["pdus"]
        if single_pdu:
            if single_pdu not in pdus_from_config(config):
                raise NotImplementedError
        self.single_pdu = single_pdu
        self.dbh = DBHandler(self.settings)

    def get_one(self):
        job = self.dbh.get_next_job(self.single_pdu)
        if job:
            job_id, hostname, port, request = job
            log.debug(job)
            log.info("Processing queue item: (%s %s) on hostname: %s",
                     request, port, hostname)
            self.do_job(hostname, port, request)
            self.dbh.delete_row(job_id)

    def driver_from_hostname(self, hostname):
        drivername = drivername_from_hostname(hostname, self.pdus)
        driver = PDUDriver.select(drivername)(hostname, self.pdus[hostname])
        return driver

    def do_job(self, hostname, port, request, delay=0):
        retries = self.settings["retries"]
        driver = False
        while retries > 0:
            try:
                driver = self.driver_from_hostname(hostname)
                return driver.handle(request, port, delay)
            except Exception as e:  # pylint: disable=broad-except
                log.warn(traceback.format_exc())
                log.warn("Failed to execute job: %s %s %s "
                         "(attempts left %i) error was %s",
                         hostname, port, request, retries, e.message)
                if driver:
                    driver._bombout()  # pylint: disable=W0212,E1101
                time.sleep(5)
                retries -= 1
        return False

    def run_me(self):
        if self.single_pdu:
            log.info("Starting a PDURunner for PDU: %s", self.single_pdu)
        else:
            log.info("Starting a PDURunner for all PDUS")
        while 1:
            self.get_one()
            time.sleep(2)
