#!/usr/bin/python3

#  Copyright 2026 Linaro Limited
#  Author Christopher Obbard <christopher.obbard@linaro.org>
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
from shutil import which
from subprocess import check_call
from pdudaemon.drivers.localbase import LocalBase

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class UHubCtl(LocalBase):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.location = settings.get("location", None)
        if not self.location:
            raise RuntimeError("uhubctl driver requires a 'location' setting")

        # Find uhubctl binary
        search_path = os.pathsep.join([
            os.environ.get("PATH", ""),
            "/sbin",
            "/usr/sbin",
            "/usr/local/sbin",
        ])
        self.uhubctl_bin = which("uhubctl", path=search_path)
        if self.uhubctl_bin is None:
            raise RuntimeError("uhubctl not found in PATH, /sbin, /usr/sbin or /usr/local/sbin")

    @classmethod
    def accepts(cls, drivername):
        if drivername == "uhubctl":
            return True
        return False

    def _port_interaction(self, command, port_number):
        try:
            port_number = int(port_number)
        except (TypeError, ValueError):
            raise RuntimeError("port_number must be an integer, got %r" % (port_number,))

        if command == "on":
            action = "on"
        elif command == "off":
            action = "off"
        else:
            log.debug("Unknown command!")
            return

        # Run uhubctl to control the port power
        cmd = [
            self.uhubctl_bin,
            "--location", str(self.location),
            "--port", str(port_number),
            "--action", str(action)
        ]
        log.debug("running %r" % cmd)
        check_call(cmd)
