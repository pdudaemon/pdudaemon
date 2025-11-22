#!/usr/bin/python3
"""CyberPower 41001 PDU driver implementation.

This driver provides support for CyberPower 41001 Power Distribution Units
using SNMP v1 protocol for remote power control.
"""

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
    """CyberPower 41001 PDU driver using SNMP v1.

    This driver controls CyberPower 41001 PDU outlets using SNMP SET commands
    with configurable community strings.
    """

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
        """Initialize CyberPower 41001 PDU driver.

        Args:
            hostname: PDU hostname or IP address
            settings: Configuration dictionary, may contain 'community' key
        """
        self.hostname = hostname
        self.settings = settings
        self.community = settings.get("community", "private")
        super().__init__(hostname, settings)

    @classmethod
    def accepts(cls, drivername):
        """Check if this driver accepts the given driver name.

        Args:
            drivername: The driver name to check

        Returns:
            bool: True if driver name is 'cyberpower41001', False otherwise
        """
        if drivername == "cyberpower41001":
            return True
        return False

    def _port_interaction(self, command, port_number):

        port_number = int(port_number)
        power_oid = f"SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.{port_number}"
        cmd_base = (
            f"/usr/bin/snmpset -v 1 -c {self.community} {self.hostname} "
            f"{power_oid} integer"
        )

        if command not in self._actions:
            log.error("Unknown command %s!", command)
            return

        cmd = f"{cmd_base} {self._actions[command]} >/dev/null"
        log.debug("running %s", cmd)
        subprocess.call(cmd, shell=True)
