#!/usr/bin/python3

#  Shelly Gen2+ driver to control second generation and later SmartPlugs, etc.
#  made by Shelly.
#
#  This does not support the secure requests through the authentication process
#  described in https://shelly-api-docs.shelly.cloud/gen2/General/Authentication.
#  Thus, this must be turned off in your Shelly device.
#
#  Based on the official Gen 2+ Device API documentation:
#  https://shelly-api-docs.shelly.cloud/gen2/General/RPCProtocol
#
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

class ShellyGen2(PDUDriver):
    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings

        super(ShellyGen2, self).__init__()

    def jsonrpc_call(self, method, params):
        r = requests.post(
            f"http://{self.hostname}/rpc",
            json = {
                "jsonrpc":"2.0",
                "id": 1,
                "method": method,
                "params": params,
            }
        )

        r.raise_for_status()
        return r.json()["result"]

    def port_get(self, port_number):
        r = self.jsonrpc_call("Switch.GetStatus", {
            "id": int(port_number)
        })
        return r["output"]

    def port_interaction(self, command, port_number):
        if not 0 <= port_number <= 3:
            raise ValueError("Invalid port number")

        if command == "get":
            return self.port_get(port_number)

        port_status = False
        if command == "on":
            port_status = True

        self.jsonrpc_call("Switch.Set", {
            "id": int(port_number),
            "on": port_status
        })

    @classmethod
    def accepts(cls, drivername):
        if drivername == "shelly_gen2":
            return True
        return False
