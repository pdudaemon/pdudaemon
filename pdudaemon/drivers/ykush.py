#!/usr/bin/python3

#  Copyright 2018 Sjoerd Simons <sjoerd.simons@collabora.co.uk>
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
from pdudaemon.drivers.driver import PDUDriver
import hid

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

YKUSH_VID = 0x04d8
YKUSH_XS_PID = 0xf0cd


class YkushXS(PDUDriver):
    connection = None
    port_count = 2
    supported = ["YKUSHXS"]

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.serial = settings.get("serial", u"")
        log.debug("serial: %s" % self.serial)

        super(YkushXS, self).__init__()

    def port_interaction(self, command, port_number):
        if port_number > self.port_count or port_number < 1:
            err = "Port should be in the range 1 - %d" % (self.port_count)
            log.error(err)
            raise RuntimeError(err)

        if command == "on":
            byte = 0x11
        elif command == "off":
            byte = 0x01
        else:
            log.error("Unknown command %s." % (command))
            return

        d = hid.device()
        d.open(YKUSH_VID, YKUSH_XS_PID, serial_number=self.serial)
        d.write([byte, byte])
        d.read(64)
        d.close()

    @classmethod
    def accepts(cls, drivername):
        return drivername in cls.supported
