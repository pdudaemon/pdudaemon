#!/usr/bin/python3

#  Copyright (c) 2023 Koninklijke Philips N.V.
#  Author Julian Haller <julian.haller@philips.com>
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
from pdudaemon.drivers.driver import PDUDriver
import os

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class Netio4(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.username = settings.get("username", "admin")
        self.password = settings.get("password", "admin")
        telnetport = settings.get("telnetport", 1234)

        self.exec_string = "/usr/bin/telnet %s %d" % (hostname, telnetport)
        super(Netio4, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        if drivername == "netio4":
            return True
        return False

    def port_interaction(self, command, port_number):
        log.debug("Running port_interaction")
        self.get_connection()
        log.debug("Attempting command: {} port: {}".format(command, port_number))
        if command == "on":
            self.connection.send("port %s 1\r" % port_number)
        elif command == "off":
            self.connection.send("port %s 0\r" % port_number)
        else:
            log.error("Unknown command")

        self.connection.expect("250 OK")

    def get_connection(self):
        log.debug("Connecting to Netio4 PDU with: %s", self.exec_string)
        self.connection = pexpect.spawn(self.exec_string)
        self._pdu_login(self.username, self.password)

    def _cleanup(self):
        if self.connection:
            self._pdu_logout()
            self.connection.close()

    def _bombout(self):
        if self.connection:
            self.connection.close(force=True)

    def _pdu_login(self, username, password):
        log.debug("attempting login with username %s, password %s", username, password)
        self.connection.send("\r")
        self.connection.expect("502 UNKNOWN COMMAND")
        self.connection.send("login %s %s\r" % (username, password))
        self.connection.expect("250 OK")

    def _pdu_logout(self):
        log.debug("Logging out")
        self.connection.send("quit\r")
        self.connection.expect("110 BYE")
