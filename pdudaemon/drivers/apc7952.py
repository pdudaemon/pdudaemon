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
from pdudaemon.drivers.apcbase import APCBase
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class APC7952(APCBase):

    @classmethod
    def accepts(cls, drivername):
        if drivername == "apc7952":
            return True
        return False

    def _pdu_logout(self):
        self._back_to_main()
        log.debug("Logging out")
        self.connection.send("4\r")

    def _back_to_main(self):
        log.debug("Returning to main menu")
        self.connection.send("\r")
        self.connection.expect('>')
        for _ in range(1, 20):
            self.connection.send("\x1B")
            self.connection.send("\r")
            res = self.connection.expect(["4- Logout", "> "])
            if res == 0:
                log.debug("Back at main menu")
                break

    def _enter_outlet(self, outlet, enter_needed=True):
        outlet = "%s" % outlet
        log.debug("Attempting to enter outlet %s", outlet)
        if enter_needed:
            self.connection.expect("Press <ENTER> to continue...")
        log.debug("Sending enter")
        self.connection.send("\r")
        self.connection.expect("> ")
        log.debug("Sending outlet number")
        self.connection.send(outlet)
        self.connection.send("\r")
        log.debug("Finished entering outlet")

    def _port_interaction(self, command, port_number):
        # make sure in main menu here
        self._back_to_main()
        self.connection.send("\r")
        self.connection.expect("1- Device Manager")
        self.connection.expect("> ")
        log.debug("Entering Device Manager")
        self.connection.send("1\r")
        self.connection.expect("------- Device Manager")
        self.connection.send("2\r")
        self.connection.expect("1- Outlet Control/Configuration")
        self.connection.expect("> ")
        self.connection.send("1\r")
        self._enter_outlet(port_number, False)
        self.connection.expect("> ")
        self.connection.send("1\r")
        res = self.connection.expect(["> ", "Press <ENTER> to continue..."])
        if res == 1:
            log.debug("Stupid paging thingmy detected, pressing enter")
            self.connection.send("\r")
        self.connection.send("\r")
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

    def _do_it(self):
        self.connection.expect("Enter 'YES' to continue or "
                               "<ENTER> to cancel :")
        self.connection.send("YES\r")
        self.connection.expect("Press <ENTER> to continue...")
        self.connection.send("\r")
