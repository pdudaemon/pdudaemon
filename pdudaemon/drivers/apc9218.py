#!/usr/bin/python3

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
from pdudaemon.drivers.apc7952 import APC7952
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class APC9218(APC7952):

    @classmethod
    def accepts(cls, drivername):
        models = ["ap9606", "apc9606", "ap9218", "apc9218"]
        if drivername.lower() in models:
            return True
        return False

    def _port_interaction(self, command, port_number):
        # make sure in main menu here
        self._back_to_main()
        self.connection.send("\r")
        self.connection.expect("1- Device Manager")
        self.connection.expect("> ")
        log.debug("Entering Device Manager")
        self.connection.send("1\r")
        self.connection.expect("------- Device Manager")
        log.debug("Got to Device Manager")
        self._enter_outlet(port_number, False)
        self.connection.expect(["1- Control Outlet",
                                "1- Outlet Control/Configuration"])
        self.connection.expect("> ")
        self.connection.send("1\r")
        res = self.connection.expect(["> ", "Press <ENTER> to continue..."])
        if res == 1:
            log.debug("Stupid paging thingmy detected, pressing enter")
            self.connection.send("\r")
        self.connection.send("\r")
        self.connection.expect(["Control Outlet %s" % port_number,
                                "Control Outlet"])
        self.connection.expect("3- Immediate Reboot")
        self.connection.expect("> ")
        if command == "on":
            self.connection.send("1\r")
            self.connection.expect("Immediate On")
            self._do_it()
        elif command == "off":
            self.connection.send("2\r")
            self.connection.expect("Immediate Off")
            self._do_it()
        else:
            log.debug("Unknown command!")
