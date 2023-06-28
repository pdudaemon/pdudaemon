#!/usr/bin/python3

#  Copyright 2016 Broadcom
#  Author Christian Daudt <csd@broadcom.com>
#  Based on apcbase+apc8959 by:
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
from pdudaemon.drivers.driver import PDUDriver
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class SynBase(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        log.debug(settings)
        self.settings = settings
        self.username = "admin"
        self.password = "admin"
        telnetport = 23

        if "telnetport" in settings:
            telnetport = settings["telnetport"]
        if "username" in settings:
            self.username = settings["username"]
        if "password" in settings:
            self.password = settings["password"]

        self.exec_string = "/usr/bin/telnet %s %d" % (hostname, telnetport)
        log.debug("Telnet command: [%s]" % self.exec_string)
        super(SynBase, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        return False

    def port_interaction(self, command, port_number):
        log.debug("Running port_interaction from SynBase")
        self.get_connection()
        log.debug("Attempting {} on port {}".format(command, port_number))
        self._port_interaction(command,  # pylint: disable=no-member
                               port_number)

    def get_connection(self):
        log.debug("Connecting to Syn PDU with: %s", self.exec_string)
        # only uncomment this line for FULL debug when developing
        # self.connection = pexpect.spawn(self.exec_string, logfile=sys.stdout)
        self.connection = pexpect.spawn(self.exec_string)
        self._pdu_login(self.username, self.password)

    def _cleanup(self):
        self._pdu_logout()  # pylint: disable=no-member

    def _bombout(self):
        log.debug("Bombing out of driver: %s", self.connection)
        self.connection.close(force=True)
        del self

    def _pdu_login(self, username, password):
        # Expected sequence:
        # >login
        # User ID: admin
        # Password:******
        # >

        log.debug("attempting login with username %s, password %s",
                  username, password)
        self.connection.expect(">")
        self.connection.send("login\r")
        self.connection.expect("User ID:")
        self.connection.send("%s\r" % username)
        self.connection.expect("Password:")
        self.connection.send("%s\r" % password)
        self.connection.expect(">")

#
# Only Synaccess product support at this point
# Synaccess Networks netBooter Series B
# Login identifies as: System Model: NP-08B


class SynNetBooter(SynBase):
    pdu_commands = {"off": "pset %s 0", "on": "pset %s 1"}

    @classmethod
    def accepts(cls, drivername):
        if drivername == "synnetbooter":
            return True
        return False

    def _pdu_logout(self):
        log.debug("logging out")
        self.connection.send("\r")
        self.connection.send("exit")
        self.connection.send("\r")
        log.debug("done")

    def _pdu_get_to_prompt(self):
        self.connection.send("\r")
        self.connection.expect('>')

    def _port_interaction(self, command, port_number):
        self._pdu_get_to_prompt()
        self.connection.sendline(self.pdu_commands[command] %
                                 (port_number))
        self._pdu_get_to_prompt()
        log.debug("done")
