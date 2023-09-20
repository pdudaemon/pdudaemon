#!/usr/bin/python3
#
#  Copyright 2022 Christopher Obbard <chris.obbard@collabora.com>
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
import os
from pdudaemon.drivers.driver import PDUDriver, FailedRequestException
import requests
from requests.auth import HTTPDigestAuth

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class ESPHomeHTTP(PDUDriver):
    def __init__(self, hostname, settings):
        """Communicate with custom devices flashed with ESPHome firmware, specifically
        Switch components (e.g. relays, GPIO).
        To use this driver, the `web_server` stanza must be defined in the ESPHome
        configuration.
        """
        self.hostname = hostname
        self.port = settings.get("port", 80)
        self.username = settings.get("username")
        self.password = settings.get("password")

        super().__init__()

    def port_interaction(self, command, esphome_entity_id):
        esphome_cmd = ""
        if command == "on":
            esphome_cmd = "turn_on"
        elif command == "off":
            esphome_cmd = "turn_off"
        else:
            raise FailedRequestException("Unknown command %s" % (command))

        # Build the POST request
        # url should be in the format http://{hostname}/switch/{id}/{cmd}
        url = "http://{}/switch/{}/{}".format(
            self.hostname, esphome_entity_id, esphome_cmd
        )
        log.debug("HTTP POST: {}".format(url))

        auth = None
        if self.username and self.password:
            auth = HTTPDigestAuth(self.username, self.password)
        response = requests.post(url, auth=auth)

        log.debug(
            "Response code for request to {}: {}".format(
                self.hostname, response.status_code
            )
        )
        response.raise_for_status()

    @classmethod
    def accepts(cls, drivername):
        return drivername == "esphome-http"
