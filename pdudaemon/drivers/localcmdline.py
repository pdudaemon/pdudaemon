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
from subprocess import call, check_output
from pdudaemon.drivers.localbase import LocalBase
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class LocalCmdline(LocalBase):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.cmd_on = settings.get("cmd_on", None)
        self.cmd_off = settings.get("cmd_off", None)
        self.cmd_state = settings.get("cmd_state", None)

    @classmethod
    def accepts(cls, drivername):
        if drivername == "localcmdline":
            return True
        return False

    def _port_interaction(self, command, port_number):
        cmd = None
        if command == "on" and self.cmd_on:
            cmd = self.cmd_on
        elif command == "off" and self.cmd_off:
            cmd = self.cmd_off
        else:
            log.debug("Unknown command!")
            return

        cmd = self._format_cmd(cmd, port_number)
        if cmd:
            log.debug("running %s" % cmd)
            call(cmd, shell=True)

    def get_port_state(self, port_number) -> bool:
        if not self.cmd_state:
            return super().get_port_state(port_number)

        cmd = self._format_cmd(self.cmd_state, port_number)
        log.debug("running %s" % cmd)
        # check_output raises CalledProcessError if cmd_state exits non-zero
        output = check_output(cmd, shell=True, text=True).strip()
        if output == "on":
            return True
        if output == "off":
            return False
        raise RuntimeError("cmd_state returned unexpected output: %r" % output)

    def _format_cmd(self, cmd, port_number):
        if "%(" in cmd:
            return cmd % dict(self.settings, hostname=self.hostname, port=port_number)
        try:
            return cmd % ()
        except TypeError:
            return cmd % port_number
