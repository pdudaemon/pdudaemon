#!/usr/bin/python3

#
#  Copyright 2021 Mark Ferry <github@markferry.net>
#
#  Based on PDUDriver:
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
from pdudaemon.drivers.driver import PDUDriver, FailedRequestException
import requests
import os

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

__manual__ = "https://s3.amazonaws.com/assets.mhint/downloads/61413/INT_163682_UM_0819_REV_5.03.pdf"


class Intellinet(PDUDriver):
    """Intellinet 163682 support.

    See also https://github.com/01programs/Intellinet_163682_IP_smart_PDU_API
    """

    port_count = 8
    endpoints = {
        "outlet": "control_outlet.htm",
    }

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.port = settings.get("port", 80)
        self.username = settings.get("username", "admin")
        self.password = settings.get("password", "admin")

        self.auth = self._auth(self.username, self.password)

        super().__init__()

    def _auth(self, username, password):
        return requests.auth.HTTPBasicAuth(username, password)

    def _api(self, page, params):
        url = "http://{}:{}/{}".format(self.hostname, self.port, page)

        log.debug("HTTP GET: {}".format(url))
        r = requests.get(url, params, auth=self.auth)

        r.raise_for_status()
        if r.text.find("401") != -1:
            log.error(r.text)
            raise FailedRequestException(r.text)
        log.debug("HTTP response: {}".format(r.text))

    def port_interaction(self, command, port_number):
        port_number = int(port_number)

        if port_number >= self.port_count or port_number < 0:
            err = "Port number must be in range 0 - {}".format(self.port_count - 1)
            log.error(err)
            raise FailedRequestException(err)

        command_map = {"on": 0, "off": 1, "reboot": 2}

        if command not in command_map:
            log.error("Unknown command %s." % (command))
            raise FailedRequestException(err)

        endpoint = self.endpoints['outlet']
        params = {"outlet{}".format(port_number): 1}
        params["op"] = command_map[command]
        params["submit"] = "Anwenden"
        self._api(endpoint, params)

    @classmethod
    def accepts(cls, drivername):
        if drivername == "intellinet":
            return True
        return False
