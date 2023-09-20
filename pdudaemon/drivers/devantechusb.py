#!/usr/bin/python3

#  Copyright 2017 Sjoerd Simons <sjoerd.simons@collabora.co.uk>
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
import serial

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class DevantechusbBase(PDUDriver):
    connection = None
    port_count = 0
    supported = []  # type: list[str]

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.device = settings.get("device", "/dev/ttyACM0")
        log.debug("device: %s" % self.device)

        super(DevantechusbBase, self).__init__()

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = "Port should be in the range 1 - %d" % (self.port_count)
            log.error(err)
            raise RuntimeError(err)

        if command == "on":
            byte = 0x64 + port_number
        elif command == "off":
            byte = 0x6e + port_number
        else:
            log.error("Unknown command %s." % (command))
            return

        s = serial.serial_for_url(self.device, 9600)
        s.write([byte])
        s.close()

    @classmethod
    def accepts(cls, drivername):
        return drivername in cls.supported


class DevantechUSB2(DevantechusbBase):
    port_count = 2
    supported = ["devantech_USB-RLY02",
                 "devantech_USB-RLY82"]


# Various 8 relay devices
class DevantechUSB8(DevantechusbBase):
    port_count = 8
    supported = ["devantech_USB-RLY08B",
                 "devantech_USB-RLY16",
                 "devantech_USB-RLY16L",
                 "devantech_USB-OPTO-RLY88",
                 "devantech_USB-OPTO-RLY816"]
