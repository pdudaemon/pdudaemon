#!/usr/bin/python3

#  Copyright 2022 Laura Nao <laura.nao@collabora.com>
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
from pdudaemon.drivers.driver import PDUDriver
from xmlrpc import client

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class Servo(PDUDriver):
    supported_ctrls = {'power_state': 'active_high',
                       'warm_reset': 'active_low',
                       'cold_reset': 'active_low'}

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings

        self.ctrls = settings.get("ctrls", ["cold_reset"])
        if not isinstance(self.ctrls, list):
            self.ctrls = [self.ctrls]

        ip = settings.get("ip", "localhost")
        port = settings.get("port", 9999)
        self.remote_uri = "http://{}:{}".format(ip, port)

        log.debug("Servod server: %s" % self.remote_uri)

        super().__init__()

    def port_interaction(self, command, port_number):
        if command not in ('on', 'off'):
            log.error("Unknown command %s." % (command))
            return

        for ctrl in self.ctrls:
            if ctrl not in self.supported_ctrls:
                err = (f'Unknown control {ctrl}. '
                       f'Available controls: {list(self.supported_ctrls.keys())}')
                raise ValueError(err)

        for ctrl in self.ctrls:
            if self.supported_ctrls[ctrl] == 'active_low':
                val = 'on' if command == 'off' else 'off'
            else:
                val = command

            log.debug("Setting %s:%s" % (ctrl, val))

            with client.ServerProxy(self.remote_uri) as proxy:
                proxy.set(ctrl, val)

    @classmethod
    def accepts(cls, drivername):
        return drivername == cls.__name__.upper()
