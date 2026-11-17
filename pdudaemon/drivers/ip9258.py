#!/usr/bin/python3

#  Copyright 2016 BayLibre, Inc.
#  Author Kevin Hilman
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
from pdudaemon.drivers.snmp import SNMP

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class IP9258(SNMP):

    def __init__(self, hostname, settings):
        super().__init__(hostname, {
            "driver": "snmpv1",
            "community": "public",
            "oid": "1.3.6.1.4.1.92.58.2.*.0",
            "onsetting": 1,
            "offsetting": 0,
        })

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ip9258":
            return True
        return False
