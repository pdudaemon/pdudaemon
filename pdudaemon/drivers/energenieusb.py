#!/usr/bin/python3

#  Copyright 2019 Martyn Welch <martyn.welch@collabora.com>
#
#  Based on devantechusb:
#     Copyright 2017 Sjoerd Simons
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
import usb.core
import usb.util

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class EnerGenieUSB(PDUDriver):
    supported = ["EG-PMS",
                 "EG-PM2"]

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.device = settings.get("device", "")
        log.debug("device: %s" % self.device)

    def port_interaction(self, command, port_number):

        devices = self.connect()

        if len(devices) == 0:
            err = "No device found"
            log.error(err)
            raise RuntimeError(err)

        dev = None
        for d in devices:
            if self.getid(d) == self.device:
                dev = d
                break
        if dev is None:
            err = "Device with id {} not found".format(self.device)
            log.error(err)
            raise RuntimeError(err)

        port_number = int(port_number)
        if port_number > 4 or port_number < 1:
            err = "Port should be in the range 1 - 4"
            log.error(err)
            raise RuntimeError(err)

        if command == "on":
            self.switchon(dev, port_number)
        elif command == "off":
            self.switchoff(dev, port_number)
        else:
            log.error("Unknown command %s." % (command))
            return

    @classmethod
    def accepts(cls, drivername):
        return drivername in cls.supported

    # Following (modified) routines taken from pysispm:
    #
    # Copyright (c) 2016, Heinrich Schuchardt <xypron.glpk@gmx.de>
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:
    #
    #     * Redistributions of source code must retain the above copyright
    #       notice, this list of conditions and the following disclaimer.
    #
    #     * Redistributions in binary form must reproduce the above copyright
    #       notice, this list of conditions and the following disclaimer in the
    #       documentation and/or other materials provided with the distribution.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    # AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    # ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
    # DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    # (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    # LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    # ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    # SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    def connect(self):
        """Returns the list of compatible devices.

        @return: device list
        """
        ret = list()
        ret += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd10))
        ret += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd11))
        ret += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd12))
        ret += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd13))
        ret += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd15))
        return ret

    def getid(self, dev):
        """Gets the id of a device.

        @return: id
        """
        buf = bytes([0x00, 0x00, 0x00, 0x00, 0x00])
        id = dev.ctrl_transfer(0xa1, 0x01, 0x0301, 0, buf, 500)
        if (len(id) == 0):
            return None
        ret = ''
        sep = ''
        for x in id:
            ret += sep
            ret += format(x, '02x')
            sep = ':'
        return ret

    def switchoff(self, dev, i):
        """Switches outlet i of the device off.

        @param dev: device
        @param i: outlet
        """
        buf = bytes([3 * i, 0x00, 0x00, 0x00, 0x00])
        buf = dev.ctrl_transfer(0x21, 0x09, 0x0300 + 3 * i, 0, buf, 500)

    def switchon(self, dev, i):
        """Switches outlet i of the device on.

        @param dev: device
        @param i: outlet
        """
        buf = bytes([3 * i, 0x03, 0x00, 0x00, 0x00])
        buf = dev.ctrl_transfer(0x21, 0x09, 0x0300 + 3 * i, 0, buf, 500)
