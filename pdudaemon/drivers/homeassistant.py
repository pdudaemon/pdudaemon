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

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class HomeAssistantHTTP(PDUDriver):
    def __init__(self, hostname, settings):
        """Communicate with devices managed by a Home Assistant instance, specifically
        Switch types.
        To use this driver, a long-lived API key must be defined as `api_key` in
        the host configuration.
        """
        self.hostname = settings.get("hostname", hostname)
        self.port = settings.get("port", 80)
        self.api_key = settings.get("api_key")

        super().__init__()

    def port_interaction(self, command, ha_entity_id):
        if command == "on":
            ha_cmd = "turn_on"
        elif command == "off":
            ha_cmd = "turn_off"
        else:
            raise FailedRequestException("Unknown command %s" % (command))

        # Build the POST request
        # url should be in the format http://{hostname}:{port}/api/services/switch/{cmd}
        url = "http://{}:{}/api/services/switch/{}".format(
            self.hostname, self.port, ha_cmd
        )
        log.debug("HTTP POST: {}".format(url))

        headers = { "Authorization": "Bearer {}".format(self.api_key) }
        body = { "entity_id": "switch.{}".format(ha_entity_id) }

        response = requests.post(url, headers=headers, json=body)

        log.debug(
            "Response code for request to {}: {}".format(
                self.hostname, response.status_code
            )
        )
        response.raise_for_status()

    @classmethod
    def accepts(cls, drivername):
        return drivername == "home-assistant-http"
