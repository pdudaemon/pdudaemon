#!/usr/bin/python3

#
#  Copyright 2023 Bob Clough <bob.clough@codethink.co.uk>
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
from pymodbus.client import ModbusTcpClient

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class ModBusTCP(PDUDriver):
    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.port = settings.get("port", 502)
        self.unit = settings.get("unit", settings.get("slave", 1))
        self._client = ModbusTcpClient(host=self.hostname, port=self.port)
        self._client.connect()
        super().__init__()

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        self._client.write_coil(address=port_number, value=(command == "on"), slave=self.unit)

    def _cleanup(self):
        self._client.close()

    @classmethod
    def accepts(cls, drivername):
        return drivername == cls.__name__.lower()
