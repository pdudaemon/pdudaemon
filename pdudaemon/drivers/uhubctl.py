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
from subprocess import check_call, check_output
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

    def _port_interaction(self, command, port):
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise RuntimeError("port must be an integer, got %r" % (port,))

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
            "--port", str(port),
            "--action", str(action)
        ]
        log.debug("running %r" % cmd)
        check_call(cmd)

    def get_port_state(self, port) -> bool:
        try:
            port = int(port)
        except (TypeError, ValueError):
            raise RuntimeError("port must be an integer, got %r" % (port,))

        # Run uhubctl to retrieve the port status
        cmd = [
            self.uhubctl_bin,
            "--location", str(self.location),
            "--port", str(port),
        ]
        log.debug("running %r" % cmd)
        output = check_output(cmd, text=True)

        prefix = "  Port %s:" % port
        for line in output.splitlines():
            if line.startswith(prefix):
                return " power" in line
        raise RuntimeError("uhubctl did not report status for port %s" % port)
