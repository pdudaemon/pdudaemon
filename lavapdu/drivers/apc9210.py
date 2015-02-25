#! /usr/bin/python

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
from lavapdu.drivers.apc7952 import APC7952


class APC9210(APC7952):

    @classmethod
    def accepts(cls, drivername):
        if drivername == "apc9210":
            return True
        return False

    def _port_interaction(self, command, port_number):
        print("Attempting command: %s port: %i" % (command, port_number))
        ### make sure in main menu here
        self._back_to_main()
        self.connection.send("\r")
        self.connection.expect("1- Outlet Manager")
        self.connection.expect("> ")
        logging.debug("Entering Outlet Manager")
        self.connection.send("1\r")
        self.connection.expect("------- Outlet Manager")
        logging.debug("Got to Device Manager")
        self._enter_outlet(port_number, False)
        self.connection.expect(["1- Control of Outlet", "1- Outlet Control/Configuration"])
        self.connection.expect("> ")
        self.connection.send("1\r")
        self.connection.expect("Turn Outlet On")
        self.connection.expect("> ")
        if command == "on":
            self.connection.send("1\r")
            self.connection.expect("Turn Outlet On")
            self._do_it()
        elif command == "off":
            self.connection.send("2\r")
            self.connection.expect("Turn Outlet Off")
            self._do_it()
        else:
            logging.debug("Unknown command!")