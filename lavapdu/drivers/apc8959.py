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
from lavapdu.drivers.apcbase import APCBase


class APC8959(APCBase):
    pdu_commands = {"off": "olOff", "on": "olOn"}

#    def __init__(self, hostname):
#        super(APC8959, self).__init__(hostname)

    @classmethod
    def accepts(cls, drivername):
        if drivername == "apc8959":
            return True
        return False

    def _pdu_logout(self):
        logging.debug("logging out")
        self.connection.send("\r")
        self.connection.send("exit")
        self.connection.send("\r")
        logging.debug("done")

    def _pdu_get_to_prompt(self):
        self.connection.send("\r")
        self.connection.expect('apc>')

    def _port_interaction(self, command, port_number):
        logging.debug("Attempting %s on port %i" % (command, port_number))
        self._pdu_get_to_prompt()
        self.connection.sendline(self.pdu_commands[command] + (" %i" % port_number))
        self.connection.expect("E000: Success")
        self._pdu_get_to_prompt()
        logging.debug("done")