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
        self.hostname = hostname
        self.username = settings.get("username")
        self.password = settings.get("password")
        super().__init__()

    def port_interaction(self, command, port_number):
        if int(port_number) > self.port_count or int(port_number) < 1:
            err = "Port number must be in range 1 - {}".format(self.port_count)
            log.error(err)
            raise FailedRequestException(err)

        params = {
            "cmnd": "Power{} {}".format(port_number, command),
            "user": self.username,
            "password": self.password
        }
        url = "http://{}/cm".format(self.hostname)
        log.debug("HTTP GET: {}".format(url))
        r = requests.get(url, params)

        # check response
        response = r.json()
        r.raise_for_status()
        expected_response_key = "POWER{}".format(port_number)
        try:
            if response[expected_response_key] != command.upper():
                log.error(response)
                raise FailedRequestException(response)
        except BaseException:
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
