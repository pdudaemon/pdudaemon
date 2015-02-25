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
import pexpect
from lavapdu.drivers.driver import PDUDriver
import sys


class APCBase(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        logging.debug(settings)
        self.settings = settings
        telnetport = 23
        if "telnetport" in settings:
            telnetport = settings["telnetport"]
        self.exec_string = "/usr/bin/telnet %s %d" % (hostname, telnetport)
        self.get_connection()
        super(APCBase, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        return False

    def port_interaction(self, command, port_number):
        logging.debug("Running port_interaction from APCBase")
        self._port_interaction(command, port_number)
        #self._cleanup()

    def get_connection(self):
        logging.debug("Connecting to APC PDU with: %s" % self.exec_string)
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            self.connection = pexpect.spawn(self.exec_string, logfile=sys.stdout)
        else:
            self.connection = pexpect.spawn(self.exec_string)
        self._pdu_login("apc","apc")

    def _cleanup(self):
        self._pdu_logout()

    def _bombout(self):
        logging.debug("Bombing out of driver: %s" % self.connection)
        self.connection.close(force=True)
        del(self)

    def _pdu_login(self, username, password):
        logging.debug("attempting login with username %s, password %s" % (username, password))
        self.connection.send("\r")
        self.connection.expect("User Name :")
        self.connection.send("%s\r" % username)
        self.connection.expect("Password  :")
        self.connection.send("%s\r" % password)
