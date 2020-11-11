#!/usr/bin/python3

#
#  Copyright 2016 BayLibre, Inc.
#  Author Kevin Hilman <khilman@kernel.org>
#
#  Based on localcmdline.py
#  Copyright 2013 Linaro Limited
#  Author Matt Hart <matthew.hart@linaro.org>
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
from pdudaemon.drivers.localbase import LocalBase
import requests

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class Sainsmart(LocalBase):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.ip = settings.get("ip", self.hostname)
        self.url_base = "http://%s/30000/" % self.ip
        log.debug(self.url_base)

    @classmethod
    def accepts(cls, drivername):
        if drivername == "sainsmart":
            return True
        return False

    def _port_interaction(self, command, port_number):

        val = -1
        if command == "on":
            log.debug("Attempting control: {} port: {}".format(command, port_number))
            val = (port_number - 1) * 2 + 1

        elif command == "off":
            log.debug("Attempting control: {} port: {}".format(command, port_number))
            val = (port_number - 1) * 2

        else:
            log.debug("Unknown command!")

        if (val >= 0):
            url = self.url_base + "%02d" % val
            log.debug("HTTP GET at %s" % url)
            requests.get(url)
