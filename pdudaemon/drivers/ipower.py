#!/usr/bin/python3
#
#  Copyright 2023 Christopher Obbard <chris.obbard@collabora.com>
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
from pdudaemon.drivers.driver import PDUDriver, FailedRequestException
import requests
from requests.auth import HTTPBasicAuth

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


# The following driver has been tested with the hardware:
#   Model No          32657
#   Firmware Version  s4.82-091012-1cb08s
# (find out by going to the web interface Information > System)
#
# Port 1 refers to Outlet A, port 2 is Outlet B and so on.
#
# To change the status of a single port, the PDU contains two cgi scripts,
# `ons.cgi` and `offs.cgi`. This script accepts a GET request with an `led`
# parameter. The led parameter should be a string representing a binary
# number, with one bit for each of the outlets, with the MSB representing
# outlet A. Only the bits which are set have their state changed.
#
# For instance:
#   ons.cgi?leds=10000000   turns on outlet A
#   offs.cgi?leds=10000000  turns off outlet A
#   ons.cgi?leds=11000000   turns on outlet A and B
#   offs.cgi?leds=11000000  turns off outlet A and B
#
# The JavaScript firmware in the WebUI pads the binary number with 0s to 24
# bits, presumably for compatibility with other models.
class LindyIPowerClassic8(PDUDriver):
    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.port = settings.get("port", 80)
        self.username = settings.get("username")
        self.password = settings.get("password")
        self.port_count = 8

        super().__init__()

    def port_interaction(self, command, port_number):
        script = ""
        if command == "on":
            script = "ons.cgi"
        elif command == "off":
            script = "offs.cgi"
        else:
            raise FailedRequestException("Unknown command %s" % (command))

        if int(port_number) > self.port_count or int(port_number) < 1:
            err = "Port number must be in range 1 - {}".format(self.port_count)
            log.error(err)
            raise FailedRequestException(err)

        # Pad the value to 24 bits and set a single bit
        port_value = 1 << (24 - int(port_number))
        port_value = "{0:024b}".format(port_value)
        params = {'led': port_value}

        url = "http://{}/{}".format(self.hostname, script)
        log.debug("HTTP GET: {}, params={}".format(url, params))

        auth = None
        if self.username and self.password:
            auth = HTTPBasicAuth(self.username, self.password)

        response = requests.get(url, params=params, auth=auth)
        log.debug(
            "Response code for request to {}: {}".format(
                self.hostname, response.status_code
            )
        )
        response.raise_for_status()

    @classmethod
    def accepts(cls, drivername):
        return drivername == "LindyIPowerClassic8"
