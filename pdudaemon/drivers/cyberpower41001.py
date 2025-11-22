#!/usr/bin/python3

#  Copyright 2025
#  Author Sean van Osnabrugge
#
#  TODO:
#  - use pysnmp instead of snmpset command-line tool
#
#  Based on cyberpower81001.py
#  Copyright 2024
#  Author Antonin Godard
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


class Cyberpower41001(LocalBase):

    _actions = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "on": 1,
        "off": 2,
        "reboot": 3,
        "cancel": 4,
    }

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.community = settings.get("community", "private")

    @classmethod
    def accepts(cls, drivername):
        if drivername == "cyberpower41001":
            return True
        return False

    def _port_interaction(self, command, port_number):

        port_number = int(port_number)
        power_oid = f"SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.{port_number}"
        cmd_base = f"/usr/bin/snmpset -v 1 -c {self.community} {self.hostname} {power_oid} integer"

        if command not in self._actions:
            log.error(f"Unknown command {command}!")
            return

        cmd = f"{cmd_base} {self._actions[command]} >/dev/null"
        log.debug("running %s" % cmd)
        subprocess.call(cmd, shell=True)
