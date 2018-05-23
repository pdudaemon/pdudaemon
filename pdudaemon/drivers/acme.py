#!/usr/bin/python3

#  Copyright 2015 BayLibre SAS
#  Author Marc Titinger <mtitinger@baylibre.com>
#
#  Based on apcxxx:
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
from pdudaemon.drivers.acmebase import ACMEBase
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class ACME(ACMEBase):

    cmd = {'on': 'dut-switch-on', 'off': 'dut-switch-off', 'reboot': 'dut-hard-reset'}

    @classmethod
    def accepts(cls, drivername):
        if drivername == "acme":
            return True
        return False

    def _pdu_logout(self):
        self._back_to_main()
        log.debug("Logging out")
        self.connection.send("exit\r")

    def _back_to_main(self):
        self.connection.send("\r")
        self.connection.expect('#')

    def _enter_outlet(self, outlet, enter_needed=True):
        log.debug("Finished entering outlet (nop)")

    def _port_interaction(self, command, port_number):
        if command not in self.cmd:
            acme_command = 'echo "unknown command {}"'.format(command)
        else:
            acme_command = '{} {}'.format(self.cmd[command], port_number)
        log.debug("Attempting command: %s", acme_command)
        self.connection.send(acme_command)
        self._do_it()
        self.connection.expect("#")

    def _do_it(self):
        self.connection.send("\r")
