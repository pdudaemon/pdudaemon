#!/usr/bin/python3

#  ubus jsonrpc interface for PoE management on OpenWrt devices. This comes in
#  handy if devices are connected to a PoE switch running OpenWrt.
#
#  The host must accept unauthenticated ubus calls for the two poe calls 'info'
#  and 'manage'.
#
#  Copyright 2025 Paul Spooren <mail@aparcar.org>
#  Copyright 2025 Jonas Jelonek <jelonek.jonas@gmail.com>
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
import os
from pdudaemon.drivers.driver import PDUDriver
import requests

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

class Ubus(PDUDriver):
    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings

        super(Ubus, self).__init__()

    def jsonrpc_call(self, path, method, message):
        r = requests.post(
            f"http://{self.hostname}/ubus",
            json = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "call",
                "params": [ "00000000000000000000000000000000", path, method, message ],
            },
        )

        r.raise_for_status()
        return r.json()["result"]

    def port_get(self, port_number):
        poe_info = self.jsonrpc_call("poe", "info", { })

        if f"lan{port_number}" not in poe_info["ports"]:
            raise RuntimeError(f"Port lan{port_number} not found in {poe_info['ports']}")

        return poe_info["ports"][f"lan{port_number}"] != "Disabled"

    def port_interaction(self, command, port_number):
        if command == "get":
            return self.port_get(port_number)

        self.jsonrpc_call(
            "poe",
            "manage",
            {
                "port": f"lan{port_number}",
                "enable": True if command == "on" else False
            }
        )

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ubus":
            return True
        return False
