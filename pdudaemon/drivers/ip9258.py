#!/usr/bin/python3

#  Copyright 2016 BayLibre, Inc.
#  Author Kevin Hilman
#
#  TODO:
#  - use pysnmp instead of snmpset command-line tool
#
#  Based on localcmdline.py
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
import subprocess
from pdudaemon.drivers.localbase import LocalBase

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class IP9258(LocalBase):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ip9258":
            return True
        return False

    def _port_interaction(self, command, port_number):
        port_number = int(port_number)
        power_oid = '1.3.6.1.4.1.92.58.2.%d.0' % (port_number)
        cmd_base = '/usr/bin/snmpset -v 1 -c public %s %s integer' \
                   % (self.hostname, power_oid)
        cmd = None

        if command == "on":
            cmd = cmd_base + ' %d > /dev/null' % (1)

        elif command == "off":
            cmd = cmd_base + ' %d > /dev/null' % (0)

        else:
            logging.debug("Unknown command!")

        if cmd:
            log.debug("running %s" % cmd)
            subprocess.call(cmd, shell=True)
