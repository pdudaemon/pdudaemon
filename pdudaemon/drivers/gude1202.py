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


class Gude1202(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        telnetport = settings.get("telnetport", 23)

        self.exec_string = "/usr/bin/telnet %s %d" % (hostname, telnetport)
        super(Gude1202, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        if drivername == "gude1202":
            return True
        return False

    def port_interaction(self, command, port_number):
        log.debug("Running port_interaction")
        self.get_connection()
        log.debug("Attempting command: {} port: {}".format(command, port_number))
        if command == "on":
            self.connection.send("port %s state set 1\r" % port_number)
        elif command == "off":
            self.connection.send("port %s state set 0\r" % port_number)
        else:
            log.error("Unknown command")

        self.connection.expect("OK.")

    def get_connection(self):
        log.debug("Connecting to Gude1202 PDU with: %s", self.exec_string)
        self.connection = pexpect.spawn(self.exec_string)

    def _cleanup(self):
        if self.connection:
            self._pdu_logout()
            self.connection.close()

    def _bombout(self):
        if self.connection:
            self.connection.close(force=True)

    def _pdu_logout(self):
        log.debug("Logging out")
        self.connection.send("quit\r")
