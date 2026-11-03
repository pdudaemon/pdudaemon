#!/usr/bin/python3

#  Copyright 2024
#  Author Antonin Godard
#
#  Based on ip9258.py
#  Copyright 2016 BayLibre, Inc.
#  Author Kevin Hilman
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
from pdudaemon.drivers.snmp import SNMP

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class Cyberpower81001(SNMP):

    def __init__(self, hostname, settings):
        super().__init__(hostname, {
            "driver": "snmpv1",
            "community": settings.get("community", "private"),
            "oid": "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4.*",
            "onsetting": 1,
            "offsetting": 2,
        })

    @classmethod
    def accepts(cls, drivername):
        if drivername in ["cyberpower81001", "cyberpower41001"]:
            return True
        return False
