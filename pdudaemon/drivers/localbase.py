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
import pexpect
from pdudaemon.drivers.driver import PDUDriver
import sys
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class LocalBase(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        super(LocalBase, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        return False

    def port_interaction(self, command, port_number):
        log.debug("Running port_interaction from LocalBase")
        self._port_interaction(command, port_number)

    def _bombout(self):
        log.debug("Bombing out of driver: %s" % self.connection)
        del(self)

    def _cleanup(self):
        log.debug("Cleaning up driver: %s" % self.connection)
