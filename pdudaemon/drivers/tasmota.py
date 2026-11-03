#!/usr/bin/python3

#  Copyright 2019 Stefan Wiehler <stefan.wiehler@missinglinkelectronics.com>
#
#  Based on PDUDriver:
#     Copyright 2013 Linaro Limited
#     Author Matt Hart <matthew.hart@linaro.org>
#
#  Protocol documentation available at:
#  https://tasmota.github.io/docs/#/Commands
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


class TasmotaBase(PDUDriver):
    port_count = None  # type: int

    def __init__(self, hostname, settings):
        self.hostname = settings.get("ip", hostname)
        self.username = settings.get("username")
        self.password = settings.get("password")
        super().__init__()

    def _power(self, port_number, command=None):
        """Send a Power command for the port and return the reported state,
        e.g. "ON" or "OFF". Without a command, the current state is queried.
        """
        if int(port_number) > self.port_count or int(port_number) < 1:
            err = "Port number must be in range 1 - {}".format(self.port_count)
            log.error(err)
            raise FailedRequestException(err)

        cmnd = "Power{}".format(port_number)
        if command is not None:
            cmnd += " {}".format(command)
        params = {
            "cmnd": cmnd,
        }

        if self.username is not None and self.password is not None:
            params["user"] = self.username
            params["password"] = self.password

        url = "http://{}/cm".format(self.hostname)
        log.debug("HTTP GET: {}".format(url))
        r = requests.get(url, params)

        # check response
        response = r.json()
        r.raise_for_status()
        expected_response_key = "POWER{}".format(port_number)
        try:
            state = response[expected_response_key]
        except BaseException:
            log.error(response)
            raise FailedRequestException(response)
        log.debug('HTTP response: {}'.format(response))
        return state

    def port_interaction(self, command, port_number):
        if self._power(port_number, command) != command.upper():
            raise FailedRequestException("Failed to turn port {} {}".format(port_number, command))

    def get_port_state(self, port_number) -> bool:
        state = self._power(port_number)
        if state not in ("ON", "OFF"):
            raise FailedRequestException("Unexpected state for port {}: {}".format(port_number, state))
        return state == "ON"

    @classmethod
    def accepts(cls, drivername):
        return False


class SonoffS20Tasmota(TasmotaBase):
    port_count = 1

    @classmethod
    def accepts(cls, drivername):
        if drivername == "sonoff_s20_tasmota":
            return True
        return False


class BrennenstuhlWSPL01Tasmota(TasmotaBase):
    port_count = 2

    @classmethod
    def accepts(cls, drivername):
        if drivername == "brennenstuhl_wspl01_tasmota":
            return True
        return False

class GenericTasmota(TasmotaBase):
    def __init__(self, hostname, settings):
        self.port_count = int(settings.get("port_count", 1))
        super().__init__(hostname, settings)

    @classmethod
    def accepts(cls, drivername):
        return drivername == "tasmota"
