#!/usr/bin/python3
#
#  Copyright 2020 Joshua Watt <JPEWhacker@gmail.com>
#
#  A driver for V-USB HID based low cost relays
#
#  See: http://vusb.wikidot.com/project:driver-less-usb-relays-hid-interface
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
import array

import os

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

VENDOR_ID = 0x16C0
PRODUCT_ID = 0x05DF
USB_TYPE_CLASS = 0x20
USB_ENDPOINT_OUT = 0x00
USB_ENDPOINT_IN = 0x80
USB_RECIP_DEVICE = 0x00
GET_REPORT = 0x1
SET_REPORT = 0x9
USB_HID_REPORT_TYPE_FEATURE = 3
MAIN_REPORT = 0


class VUSBHID(PDUDriver):
    def __init__(self, hostname, settings):
        self.settings = settings
        self.serial = settings.get("serial", "")
        self.invert = settings.get("invert", False)
        log.debug("serial: %s" % self.serial)

    def port_interaction(self, command, port_number):
        def xor(a, b):
            return bool(a) != bool(b)

        devices = self.connect()

        if len(devices) == 0:
            err = "No device found"
            log.error(err)
            raise RuntimeError(err)

        dev = None
        for d in devices:
            product = usb.util.get_string(d, d.iProduct)
            if not product.startswith("USBRelay"):
                continue

            data = self.get_report(d, MAIN_REPORT, 8)
            serial = data[0:5].tobytes().decode("utf-8")

            if serial == self.serial:
                dev = d
                break
        else:
            err = "Device with serial {} not found".format(self.serial)
            log.error(err)
            raise RuntimeError(err)

        port_number = int(port_number)

        # The end of the product string indicates the number of relays
        max_ports = int(product[8:])

        if port_number > max_ports or port_number < 1:
            err = "Port should be in the range 1 - {}".format(max_ports)
            log.error(err)
            raise RuntimeError(err)

        if command == "on":
            self.set_state(dev, port_number, xor(True, self.invert))
        elif command == "off":
            self.set_state(dev, port_number, xor(False, self.invert))
        else:
            log.error("Unknown command %s." % (command))
            return

    @classmethod
    def accepts(cls, drivername):
        return drivername == "vusbhid"

    def connect(self):
        ret = list()
        ret += list(usb.core.find(find_all=True, idVendor=0x16C0, idProduct=0x05DF))
        return ret

    def set_state(self, dev, port, state):
        buf = array.array("B")
        buf.append(0xFF if state else 0xFD)
        buf.append(port)
        dev.ctrl_transfer(
            USB_TYPE_CLASS | USB_RECIP_DEVICE | USB_ENDPOINT_OUT,
            SET_REPORT,
            (USB_HID_REPORT_TYPE_FEATURE << 8) | MAIN_REPORT,
            0,
            buf,
            5000,
        )

    def get_report(self, dev, report, size):
        return dev.ctrl_transfer(
            USB_TYPE_CLASS | USB_RECIP_DEVICE | USB_ENDPOINT_IN,
            GET_REPORT,
            (USB_HID_REPORT_TYPE_FEATURE << 8) | report,
            0,
            size,
            5000,
        )
