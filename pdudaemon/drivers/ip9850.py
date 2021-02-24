#!/usr/bin/python3

#
#  Copyright 2019 Stefan Wiehler <stefan.wiehler@missinglinkelectronics.com>
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


class ip9850(PDUDriver):
    port_count = 4

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.username = settings.get("username")
        self.password = settings.get("password")
        super().__init__()

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = "Port number must be in range 1 - {}".format(self.port_count)
            log.error(err)
            raise FailedRequestException(err)
        if command == "on":
            pwr = "1"
        elif command == "off":
            pwr = "0"
        else:
            log.error("Unknown command %s." % (command))
            return

        params = {
            "user": self.username,
            "pass": self.password,
            "cmd": "setpower",
            "p6{}".format(port_number): "{}".format(pwr)
        }
        url = "http://{}/set.cmd".format(self.hostname)
        log.debug("HTTP GET: {}".format(url))
        r = requests.get(url, params)

        r.raise_for_status()
        if r.text.find("401") != -1:
            log.error(r.text)
            raise FailedRequestException(r.text)
        log.debug('HTTP response: {}'.format(r.text))

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ip9850":
            return True
        return False
