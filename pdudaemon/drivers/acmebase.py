#!/usr/bin/python3

#  Copyright 2015 BayLibre SAS
#  Author Marc Titinger <mtitinger@baylibre.com>
#
#  Based on ACPBase:
#     Copyright 2013 Linaro Limited
#     Author Matt Hart <matthew.hart@linaro.org>
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

# SSH connection, assuming the id_rsa.pub key for the owner of pdudaemon-runner
# i.e. root, was added to the authorized_keys on the ACME device.
# This may be changed to a simple telnet connection in the future.


class ACMEBase(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.username = settings.get("username", "root")
        self.exec_string = "/usr/bin/ssh %s@%s" % (self.username, hostname)
        super(ACMEBase, self).__init__()

    @classmethod
    def accepts(cls, drivername):  # pylint: disable=unused-argument
        return False

    def port_interaction(self, command, port_number):
        log.debug("Running port_interaction from ACMEBase")
        self.get_connection()
        self._port_interaction(command,  # pylint: disable=no-member
                               port_number)

    def get_connection(self):
        log.debug("Connecting to Baylibre ACME with: {}".format(self.exec_string))
        # only uncomment this line for FULL debug when developing
        # self.connection = pexpect.spawn(self.exec_string, logfile=sys.stdout)
        self.connection = pexpect.spawn(self.exec_string)
        self._pdu_login(self.username, "")

    def _cleanup(self):
        self._pdu_logout()  # pylint: disable=no-member

    def _bombout(self):
        log.debug("Bombing out of driver: {}".format(self.connection))
        self.connection.close(force=True)
        del self

    def _pdu_login(self, username, password):
        log.debug("attempting login with username %s, password %s",
                  username, password)
        index = self.connection.expect(['#', 'password', 'yes/no'])
        if index == 1:
            self.connection.send("%s\r" % password)
        elif index == 2:
            self.connection.send("yes\r")
