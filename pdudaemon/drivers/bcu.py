#!/usr/bin/python3

#  Copyright 2020 NXP
#  Author Leonard Crestez <leonard.crestez@nxp.com>
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

from pdudaemon.drivers.driver import PDUDriver
import os
import subprocess
import logging
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class BCU(PDUDriver):
    """PDUDriver implementation using NXP BCU.

    The NXP BCU tool can be used for remote power control on some newer NXP
    development boards.

    See https://github.com/NXPmicro/bcu
    """

    @classmethod
    def accepts(cls, drivername):
        return drivername == "bcu"

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings

        #: usb path (string "like 3-7.1")
        self.id = settings.get('id', None)
        #: board id (see `bcu lsboard`)
        self.board = settings.get('board', None)
        #: path to bcu executable (default assumes bcu is in $PATH)
        self.bcu_exe = settings.get('bcu_exe', 'bcu')
        #: gpio used for reset function (see `bcu lsgpio -gpio=$gpio`)
        self.reset_gpio = settings.get('reset_gpio', 'reset')
        #: if reset_gpio is active low (default True)
        self.reset_gpio_active_low = bool(int(
            settings.get('reset_gpio_active_low', '1')))

        #: bootmode to initialize (see `bcu lsbootmode -board=$board`)
        self.bootmode = settings.get('bootmode', None)

    def _run(self, subcmd):
        cmd = [self.bcu_exe]
        cmd += subcmd
        if self.id:
            cmd += ['-id=' + self.id]
        if self.board:
            cmd += ['-board=' + self.board]
        log.info('RUN: %s', ' '.join(cmd))
        return subprocess.run(cmd, check=True)

    def _init(self):
        return self._run(['init'] + [self.bootmode] if self.bootmode else [])

    def _set_gpio(self, gpio, value):
        return self._run(['set_gpio', gpio, value])

    def port_on(self, port_number):
        self._init()
        self._set_gpio(
            self.reset_gpio,
            '1' if self.reset_gpio_active_low else '0')

    def port_off(self, port_number):
        self._init()
        self._set_gpio(
            self.reset_gpio,
            '0' if self.reset_gpio_active_low else '1')
