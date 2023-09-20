#!/usr/bin/python3

#  Copyright 2022 Sjoerd Simons <sjoerd@collabora.com>
#  Copyright 2023 Sietze van Buuren <Sietze.vanBuuren@de.bosch.com>
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
import time
import hid
from pdudaemon.drivers.driver import PDUDriver
from pdudaemon.drivers.hiddevice import HIDDevice


log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

CLEWARE_VID = 0x0d50
CLEWARE_SWITCH1_PID = 0x0008
CLEWARE_CONTACT00_PID = 0x0030
CLEWARE_NEW_SWITCH_SERIAL = 0x63813


class ClewareBase(PDUDriver):
    """Base class for Cleware USB-Switch drivers."""
    switch_pid = None  # type: int
    connection = None
    port_count = 0

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.serial = int(settings.get("serial", u""))
        log.debug("serial: %s", self.serial)
        super().__init__()

    def new_switch_serial(self, device_path):
        """Find the correct serial for novel Cleware USB Switch devices."""
        with HIDDevice(path=device_path) as dev:
            serial = 0
            for i in range(8, 15):
                b = int(chr(self.read_byte(dev, i)), 16)
                serial *= 16
                serial += b
        return serial

    def device_path(self):
        """Search and return the matching device path."""
        for dev_dict in hid.enumerate(CLEWARE_VID, self.switch_pid):
            device_path = dev_dict['path']
            serial_compare = int(dev_dict["serial_number"], 16)
            if self.serial == serial_compare:
                return device_path
            if serial_compare == CLEWARE_NEW_SWITCH_SERIAL:
                serial_candidate = self.new_switch_serial(device_path)
                log.debug("Considering serial number match: %s", serial_candidate)
                if self.serial == serial_candidate:
                    return device_path
                continue
        err = f"Cleware device with serial number {self.serial} not found!"
        log.error(err)
        raise RuntimeError(err)

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


class ClewareSwitch1Base(ClewareBase):
    switch_pid = CLEWARE_SWITCH1_PID

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = f"Port should be in the range 1 - {self.port_count}"
            log.error(err)
            raise RuntimeError(err)

        port = 0x10 + port_number - 1
        if command == "on":
            on = 1
        elif command == "off":
            on = 0
        else:
            log.error("Unknown command %s.", (command))
            return

        with HIDDevice(path=self.device_path()) as dev:
            dev.write([0, 0, port, on])


class ClewareUsbSwitch4(ClewareSwitch1Base):
    port_count = 4


class ClewareContact00Base(ClewareBase):
    switch_pid = CLEWARE_CONTACT00_PID

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = f"Port should be in the range 1 - {self.port_count}"
            log.error(err)
            raise RuntimeError(err)

        port = 1 << (port_number - 1)
        if command == "on":
            on = port
        elif command == "off":
            on = 0
        else:
            log.error("Unknown command %s.", (command))
            return

        with HIDDevice(path=self.device_path()) as dev:
            dev.write([0, 3, on >> 8, on & 0xff, port >> 8, port & 0xff])


class ClewareUsbSwitch8(ClewareContact00Base):
    port_count = 8
