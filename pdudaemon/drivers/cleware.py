#!/usr/bin/python3

#  Copyright 2022 Sjoerd Simons <sjoerd@collabora.com>
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
from pdudaemon.drivers.hiddevice import HIDDevice
import os
import time

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

CLEWARE_VID = 0x0d50
CLEWARE_SWITCH1_PID = 0x0008
CLEWARE_CONTACT00_PID = 0x0030
CLEWARE_SWITCH4_SERIAL = 0x63813


class ClewareSwitch1Base(PDUDriver):
    connection = None
    port_count = 0

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.serial = int(settings.get("serial", u""))
        log.debug("serial: %s" % self.serial)
        super().__init__()

    def switch4_serial(self, dev_dict):
        dev = hid.device()
        dev.open_path(dev_dict["path"])
        serial = 0
        for i in range(8, 15):
            b = int(chr(self.read_byte(dev, i)), 16)
            serial *= 16
            serial += b
        dev.close()
        return serial

    def device_path(self):
        for dev_dict in hid.enumerate(CLEWARE_VID, CLEWARE_SWITCH1_PID):
            if int(dev_dict["serial_number"], 16) != CLEWARE_SWITCH4_SERIAL:
                continue
            if self.serial == self.switch4_serial(dev_dict):
                return dev_dict['path']
        err = f"Cleware device with serial number {self.serial} not found!"
        log.error(err)
        raise RuntimeError(err)

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = "Port should be in the range 1 - %d" % (self.port_count)
            log.error(err)
            raise RuntimeError(err)

        port = 0x10 + port_number - 1
        if command == "on":
            on = 1
        elif command == "off":
            on = 0
        else:
            log.error("Unknown command %s." % (command))
            return

        with HIDDevice(path=self.device_path()) as d:
            d.write([0, 0, port, on])

    @staticmethod
    def read_byte(dev, addr):
        dev.write([0, 2, addr])
        while True:
            data = dev.read(16)
            if data[4] == addr:
                return data[5]
            time.sleep(0.01)

    @classmethod
    def accepts(cls, drivername):
        return drivername.lower() == cls.__name__.lower()


class ClewareUsbSwitch4(ClewareSwitch1Base):
    port_count = 4


class ClewareContact00Base(PDUDriver):
    connection = None
    port_count = 0

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.serial = int(settings.get("serial", u""))
        log.debug("serial: %s" % self.serial)
        super().__init__()

    def find_hid_serial(self):
        for dev_dict in hid.enumerate(CLEWARE_VID, CLEWARE_CONTACT00_PID):
            serial_number = dev_dict['serial_number']
            if self.serial == int(serial_number, 16):
                return serial_number
        err = f"Cleware device with serial number {self.serial} not found"
        log.error(err)
        raise RuntimeError(err)

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = "Port should be in the range 1 - %d" % (self.port_count)
            log.error(err)
            raise RuntimeError(err)

        port = 1 << (port_number - 1)
        if command == "on":
            on = port
        elif command == "off":
            on = 0
        else:
            log.error("Unknown command %s." % (command))
            return

        with HIDDevice(CLEWARE_VID, CLEWARE_CONTACT00_PID, serial=self.find_hid_serial()) as d:
            d.write([0, 3, on >> 8, on & 0xff, port >> 8, port & 0xff])

    @classmethod
    def accepts(cls, drivername):
        return drivername.lower() == cls.__name__.lower()


class ClewareUsbSwitch8(ClewareContact00Base):
    port_count = 8
