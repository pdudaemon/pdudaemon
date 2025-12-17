#!/usr/bin/python3

#  Copyright: 2024 Collabora Limited
#  Author: Dave Pigott <dave.pigott"collabora.com>
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
import os
import serial

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class CambrionixBase(PDUDriver):
    connection = None
    port_count = 0

    def __init__(self, hostname, settings):
        super(CambrionixBase, self).__init__()
        self.settings = settings
        self.hubid = settings.get("hubid")
        self.shell_prompt = settings.get("shell_prompt", ">>")
        self.retries = settings.get("retries", 5)
        self.mode_map = {"off": "o", "on": "c"}
        self.state_map = {"Idle": {"state": "I", "mode": "sync"},
                          "Charge": {"state": "C", "mode": "sync"},
                          "Finished": {"state": "F", "mode": "sync"},
                          "Detached": {"state": "c", "mode": "sync"},
                          "off": {"state": "O", "mode": "off"}}

    def connect(self):
        try:
            self.connection = serial.serial_for_url("/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_%s-if00-port0" % self.hubid, 115200)
        except FileNotFoundError:
            err = "No such device found"
            log.error(err)
            raise RuntimeError(err)

    def set_port_state(self, connection, port_no, mode):
        mode_char = self.mode_map[mode]
        command = "mode %s %s\r\n" % (mode_char, port_no)
        self.connection.write(command.encode('utf-8'))
        log.debug("Port %s now set to %s" % (port_no, mode_char))

    def port_interaction(self, command, port_number):
        self.connect()
        port_number = int(port_number)
        if port_number > self.port_count:
            log.error("Port number requested %s is higher than the available port count (%s)" % (port_number, self.port_count))
            raise RuntimeError("Port number requested %s is higher than the available port count (%s)" % (port_number, self.port_count))
        self.set_port_state(self.connection, port_number, command)

    def _close_connection(self):
        # Logout
        log.debug("Closing connection.")
        self.connection.close()

    def _cleanup(self):
        self._close_connection()

    def _bombout(self):
        self._close_connection()

    @classmethod
    def accepts(cls, drivername):
        return False

class CambrionixPDSyncC4(CambrionixBase):
    port_count = 4

    @classmethod
    def accepts(cls, drivername):
        if drivername == "cambrionix_pdsyncc4":
            return True
        return False
