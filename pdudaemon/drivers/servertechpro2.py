#!/usr/bin/python3

#  Copyright 2020 Arm Limited
#  Author Malcolm Brooks <malcolm.brooks@arm.com>
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

import json
import logging
import os

import requests

from pdudaemon.drivers.localbase import LocalBase

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class ServerTechPro2(LocalBase):

    DEFAULT_TIMEOUT = 60

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.username = settings.get("username", "admin")
        self.password = settings.get("password", "admin")
        self.timeout = ServerTechPro2.DEFAULT_TIMEOUT
        try:
            self.timeout = float(
                settings.get("timeout", ServerTechPro2.DEFAULT_TIMEOUT)
            )
        except ValueError:
            pass

        self.insecure = bool(settings.get("insecure", False))

        protocol = settings.get("protocol", "http")
        server_address = settings.get("ip", self.hostname)
        self.url_base = "{}://{}/jaws/control/outlets/".format(
            protocol, server_address)

    @classmethod
    def accepts(cls, drivername):
        if drivername == "servertechpro2":
            return True
        return False

    def _port_interaction(self, command, port_number):
        log.debug("Attempting command: '{}' port: '{}'".format(command, port_number))
        if command in ("on", "off"):
            if self.insecure:
                requests.packages.urllib3.disable_warnings()
            url = "{}{}".format(self.url_base, port_number)
            data = {"control_action": command}
            r = requests.patch(
                url=url,
                data=json.dumps(data),
                auth=(self.username, self.password),
                headers={"Content-Type": "application/json"},
                verify=not self.insecure,
                timeout=self.timeout,
            )
            r.raise_for_status()
            log.debug("Done with command: '{}' port: '{}'".format(command, port_number))
        else:
            log.debug(
                "Unknown command for: '{}' port: '{}'".format(command, port_number)
            )
