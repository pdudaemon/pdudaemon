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
    """Driver for power outlets running Tasmota firmware.

    Supported settings:
      ip          IP address or hostname of the device (default: PDU name)
      port_count  number of controllable outlets (default depends on model)
      timeout     HTTP timeout in seconds (default: 10)
      username    web interface username (optional, firmware < 9.2)
      password    web interface password (optional, firmware < 9.2)

    The device is controlled via the legacy web command endpoint,
    e.g. GET http://<ip>/cm?cmnd=Power1+On . Reply format depends on
    the firmware version and number of outlets:
      - firmware < 12, or multi outlet devices: {"POWER1": "ON"}
      - single outlet devices (firmware >= 12):  {"POWER": "ON"}
    Both variants are accepted.
    """
    port_count = None  # type: int

    def __init__(self, hostname, settings):
        self.hostname = settings.get("ip", hostname)
        self.username = settings.get("username")
        self.password = settings.get("password")
        self.timeout = int(settings.get("timeout", 10))
        super().__init__()

    def port_interaction(self, command, port_number):
        if int(port_number) > self.port_count or int(port_number) < 1:
            err = "Port number must be in range 1 - {}".format(self.port_count)
            log.error(err)
            raise FailedRequestException(err)

        params = {
            "cmnd": "Power{} {}".format(port_number, command),
        }

        if self.username is not None and self.password is not None:
            params["user"] = self.username
            params["password"] = self.password

        url = "http://{}/cm".format(self.hostname)
        log.debug("HTTP GET: {}".format(url))
        r = requests.get(url, params, timeout=self.timeout)

        # check response
        response = r.json()
        r.raise_for_status()
        # Tasmota replies with "POWER<n>" for multi outlet devices and
        # with "POWER" for single outlet devices (firmware >= 12).
        response_value = None
        for response_key in ("POWER{}".format(port_number), "POWER"):
            if response_key in response:
                response_value = response[response_key]
                break
        if response_value is None:
            log.error(response)
            raise FailedRequestException(response)
        # "Power<n> Get" echoes "GET" on multi outlet devices but
        # reports the outlet state on single outlet devices.
        expected = command.upper()
        if command.lower() == "get":
            expected_values = ("GET", "ON", "OFF")
        else:
            expected_values = (expected,)
        if response_value not in expected_values:
            log.error(response)
            raise FailedRequestException(response)
        log.debug('HTTP response: {}'.format(response))

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
