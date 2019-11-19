#!/usr/bin/python3

#  Copyright 2019 Stefan Wiehler <stefan.wiehler@missinglinkelectronics.com>
#
#  Based on PDUDriver:
#     Copyright 2013 Linaro Limited
#     Author Matt Hart <matthew.hart@linaro.org>
#
#  Protocol documentation (in German) available at:
#  https://forum.anel.eu/viewtopic.php?f=52&t=888&sid=a0aca2195ffff4eb28a11fd89898590b
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


class AnelNETPwrCtrlBase(PDUDriver):
    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.username = settings.get("username", "admin")
        self.password = settings.get("password", "anel")
        super().__init__()

    def port_interaction(self, command, port_number):
        if port_number > self.port_count or port_number < 1:
            err = "Port number must be in range 1 - {}".format(self.port_count)
            log.error(err)
            raise FailedRequestException(err)

        url = "http://{}?Sw_{}={},{}{}".format(
            self.hostname, command, port_number, self.username, self.password)
        log.debug("HTTP GET: {}".format(url))
        r = requests.get(url)

        r.raise_for_status()
        if r.text == "User or password error.":
            log.error(r.text)
            raise FailedRequestException(r.text)
        log.debug('HTTP response: {}'.format(r.text))

    @classmethod
    def accepts(cls, drivername):
        return False


class AnelNETPwrCtrlHOME(AnelNETPwrCtrlBase):
    port_count = 3

    @classmethod
    def accepts(cls, drivername):
        if drivername == "anel_netpwrctrlhome":
            return True
        return False


class AnelNETPwrCtrlADV(AnelNETPwrCtrlBase):
    port_count = 8

    @classmethod
    def accepts(cls, drivername):
        if drivername == "anel_netpwrctrladv":
            return True
        return False


class AnelNETPwrCtrlIO(AnelNETPwrCtrlBase):
    port_count = 8

    @classmethod
    def accepts(cls, drivername):
        if drivername == "anel_netpwrctrlio":
            return True
        return False


class AnelNETPwrCtrlPRO(AnelNETPwrCtrlBase):
    port_count = 8

    @classmethod
    def accepts(cls, drivername):
        if drivername == "anel_netpwrctrlpro":
            return True
        return False
