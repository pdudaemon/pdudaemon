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
from driver import PDUDriver
import sys

class APCBase(PDUDriver):
    connection = None

    def __init__(self, pdu_hostname, pdu_telnetport=23):
        self.exec_string = "/usr/bin/telnet %s %d" % (pdu_hostname, pdu_telnetport)
        self.get_connection()
        super(APCBase, self).__init__(pdu_hostname)

    #def port_on(self, port_number):
    #    self.port_interaction("on", port_number)

    #def port_off(self, port_number):
    #    self.port_interaction("off", port_number)

    def port_interaction(self, command, port_number):
        logging.debug("Running port_interaction from APCBase")
        self._port_interaction(command, port_number)
        self._cleanup()

    def get_connection(self):
        logging.debug("Connecting to APC PDU with: %s" % self.exec_string)
        self.connection = pexpect.spawn(self.exec_string, logfile=sys.stdout)
        self._pdu_login("apc","apc")

    def _cleanup(self):
        self._pdu_logout()
        logging.debug("Closing connection: %s" % self.connection)
        self.connection.close(True)
        del(self)

    def _pdu_login(self, username, password):
        logging.debug("attempting login with username %s, password %s" % (username, password))
        self.connection.send("\r")
        self.connection.expect("User Name :")
        self.connection.send("%s\r" % username)
        self.connection.expect("Password  :")
        self.connection.send("%s\r" % password)
