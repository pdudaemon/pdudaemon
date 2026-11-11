#!/usr/bin/python3

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
from pdudaemon.drivers.localbase import LocalBase

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class SysfsGPIO(LocalBase):
    """Switch power through GPIO lines of the local host.

    Uses the sysfs GPIO interface (/sys/class/gpio) and exports the line if
    needed.

    Settings:
      chip: label of the gpiochip (see /sys/class/gpio/gpiochip*/label),
        e.g. "pinctrl-rp1" on a Raspberry Pi 5. The port number is then the
        line on that chip (the BCM number on a Raspberry Pi). Without it, the
        port number is the global sysfs GPIO number, like the 'index' of
        labgrid's SysfsGPIO resource. The kernel assigns those at boot, so
        they can change between kernel versions.
      invert: true if the line is active low, so 'on' drives it low.
    """

    sysfs_path = "/sys/class/gpio"

    def __init__(self, hostname, settings):
        super(SysfsGPIO, self).__init__(hostname, settings)
        invert = settings.get("invert", False)
        if not isinstance(invert, bool):
            raise RuntimeError("sysfsgpio 'invert' must be true or false, got %r" % (invert,))
        self.invert = invert
        chip = settings.get("chip")
        if chip is not None and (not isinstance(chip, str) or not chip):
            raise RuntimeError("sysfsgpio 'chip' must be a gpiochip label, got %r" % (chip,))
        self.chip = chip

    @classmethod
    def accepts(cls, drivername):
        return drivername == "sysfsgpio"

    def _read(self, *path):
        with open(os.path.join(self.sysfs_path, *path)) as fd:
            return fd.read().strip()

    def _chip_range(self):
        # Looked up on every request: the base is assigned at boot and differs
        # between kernels (e.g. 399 and 571 for the Raspberry Pi 5's RP1).
        found = []
        for name in sorted(os.listdir(self.sysfs_path)):
            if name.startswith("gpiochip") and self._read(name, "label") == self.chip:
                found.append((int(self._read(name, "base")), int(self._read(name, "ngpio"))))
        if not found:
            raise RuntimeError("no gpiochip labelled %r" % self.chip)
        if len(found) > 1:
            raise RuntimeError("%d gpiochips labelled %r" % (len(found), self.chip))
        return found[0]

    def _gpio_path(self, index):
        path = os.path.join(self.sysfs_path, "gpio%d" % index)
        if not os.path.exists(path):
            log.debug("exporting GPIO %d", index)
            with open(os.path.join(self.sysfs_path, "export"), "w") as export:
                export.write(str(index))
            if not os.path.exists(path):
                raise RuntimeError("GPIO %d not found after export" % index)
        return path

    def _port_interaction(self, command, port_number):
        try:
            index = int(port_number)
        except (TypeError, ValueError):
            raise RuntimeError("port_number must be a GPIO number, got %r" % (port_number,))
        if index < 0:
            raise RuntimeError("port_number must be a GPIO number, got %r" % (port_number,))

        if command == "on":
            high = not self.invert
        elif command == "off":
            high = self.invert
        else:
            log.debug("Unknown command!")
            return

        if self.chip:
            base, ngpio = self._chip_range()
            if index >= ngpio:
                raise RuntimeError("%s has %d lines, no line %d" % (self.chip, ngpio, index))
            log.debug("%s line %d is GPIO %d", self.chip, index, base + index)
            index += base

        # Writing "high" or "low" to direction makes the line an output with
        # that level in one step, so it doesn't glitch when it was an input.
        # The level is raw, so 'active_low' set by other users doesn't matter.
        level = "high" if high else "low"
        direction = os.path.join(self._gpio_path(index), "direction")
        log.debug("setting GPIO %d %s", index, level)
        with open(direction, "w") as fd:
            fd.write(level)
