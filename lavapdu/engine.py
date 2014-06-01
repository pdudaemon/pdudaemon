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
import pkgutil
import sys


class PDUEngine():
    connection = None
    prompt = 0
    driver = None
    firmware_dict = {}

    def __init__(self, pdu_hostname, pdu_telnetport=23):
        self.exec_string = "/usr/bin/telnet %s %d" % (pdu_hostname, pdu_telnetport)
        logging.debug("Created new PDUEngine: %s" % self.exec_string)
        required_version = self._pdu_login("apc", "apc")
        logging.debug("Got firmware version: %s" % required_version)
        driver_list = self.load_all_modules_from_dir("drivers")
        for driver in driver_list:
            handled = []
            exec("handled = %s.Meta.handled_firmware" % driver)
            for firmware_value in handled:
                self.firmware_dict[firmware_value] = driver

        logging.debug("Firmware versions supported: %s" % self.firmware_dict)
        if self.firmware_dict[required_version]:
            driver = self.firmware_dict[required_version]
            logging.debug("Using driver %s for version: %s" % (driver, required_version))
            exec("self.driver = %s(self.connection)" % driver)
        else:
            self.driver = None

    def load_all_modules_from_dir(self, dirname):
        module_list = []
        for importer, package_name, _ in pkgutil.iter_modules([dirname]):
            full_package_name = '%s.%s' % (dirname, package_name)
            if full_package_name not in sys.modules and (not full_package_name == "%s.driver" % dirname):
                import_string = "global %s\nfrom %s import %s" % (package_name,full_package_name,package_name)
                exec (import_string)
                logging.debug(import_string)
            if (not full_package_name == "%s.driver" % dirname):
                module_list.append(package_name)
        return module_list

    def pduconnect(self):
        self.connection = self.get_connection(self.exec_string)

    def pduclose(self):
        logging.debug("Closing connection: %s" % self.connection)
        self.connection.close(True)

    def pdureconnect(self):
        self.pduclose()
        self.pduconnect()

    def get_connection(self, exec_string):
        connection = pexpect.spawn(exec_string)
        #connection.logfile = sys.stdout
        return connection

    def is_busy(self):
        if os.path.exists("/proc/%i" % self.connection.pid):
            return True
        return False

    def close(self):
        self.driver._pdu_logout()
        self.firmware_dict = {}
        del(self)

    def _pdu_login(self, username, password):
        logging.debug("attempting login with username %s, password %s" % (username, password))
        self.pduconnect()
        self.connection.send("\r")
        self.connection.expect("User Name :")
        self.connection.send("apc\r")
        self.connection.expect("Password  :")
        self.connection.send("apc\r")
        output = self.connection.read(250)
        #print "OUTPUT: %s" % output
        a = output.split("AOS")[1].split()[0]
        #print "A: %s" % a
        b = a.strip()
        #print "B: %s" % b
        version = b
        return version.strip()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    pe = PDUEngine("pdu01")
    pe.driver.port_off(1)
    pe.driver.port_on(1)
    pe.close()
    pe = PDUEngine("pdu03")
    pe.driver.port_off(3)
    pe.driver.port_on(3)
    pe.close()

    #pe = PDUEngine("pdu16")
    #pe.close()