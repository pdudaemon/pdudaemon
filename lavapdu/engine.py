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

import pexpect
import os
import logging

from apcdrivers import apc8959
from apcdrivers import apc7952


class PDUEngine():
    connection = None
    prompt = 0
    driver = None
    USERNAME = "apc"
    PASSWORD = "apc"

    def __init__(self, pdu_hostname, pdu_telnetport = 23):
        self.exec_string = "/usr/bin/telnet %s %d" % (pdu_hostname, pdu_telnetport)
        logging.debug("Created new PDUEngine: %s" % self.exec_string)
        #self.connection.logfile_read = sys.stdout
        prompt = self._pdu_login(self.USERNAME,self.PASSWORD)
        if prompt == 0:
            logging.debug("Found a v5 prompt")
            self.driver = apc8959(self.connection)
        elif prompt == 1:
            logging.debug("Found a v3 prompt")
            self.driver = apc7952(self.connection)
        else:
            logging.debug("Unknown prompt!")

    def pduconnect(self):
        self.connection = self.get_connection(self.exec_string)

    def pduclose(self):
        self.connection.close(True)

    def pdureconnect(self):
        self.pduclose()
        self.pduconnect()

    def get_connection(self, exec_string):
        connection = pexpect.spawn(exec_string)
        return connection

    def is_busy(self):
        if os.path.exists("/proc/%i" % self.connection.pid):
            return True
        return False

    def close(self):
        self.driver._pdu_logout()
        self.connection.close(True)

    def _pdu_login(self, username, password):
        logging.debug("attempting login with username %s, password %s" % (username,password))
        self.pduconnect()
        self.connection.send("\r")
        self.connection.expect ("User Name :")
        self.connection.send("%s\r" % username)
        self.connection.expect("Password  :")
        self.connection.send("%s\r" % password)
        return self.connection.expect(["apc>", ">"])


if __name__ == "__main__":
    pe1 = PDUEngine("pdu15")
    pe1.driver.port_off(22)
    pe1.driver.port_on(22)
    pe1.close()
    pe2 = PDUEngine("pdu14")
    pe2.driver.port_off(6)
    pe2.driver.port_on(6)
    pe2.close()
    pe3 = PDUEngine("pdu01")
    pe3.driver.port_reboot(1)
    pe3.driver.port_off(1)
    pe3.driver.port_on(1)
    pe3.close()
    pe4 = PDUEngine("pdu02")
    pe4.driver.port_reboot(8)
    pe4.driver.port_off(8)
    pe4.driver.port_on(8)
    pe4.close()

