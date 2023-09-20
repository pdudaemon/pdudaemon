#!/usr/bin/python3

#  Copyright 2023 Sietze van Buuren <sietze.vanbuuren@de.bosch.com>
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

import os
import logging
import hid

log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class HIDDevice:
    def __init__(self, vid=None, pid=None, serial=None, path=None):
        self.__dev = hid.device()
        if path:
            self.__dev.open_path(path)
        elif serial:
            self.__dev.open(vid, pid, serial)
        elif pid and vid:
            self.__dev.open(vid, pid, None)
        else:
            err = "Unable to open HID device"
            log.error(err)
            raise RuntimeError(err)

    def __enter__(self):
        """Open and Return HID Device."""
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Close HID Device."""
        self.__dev.close()

    def write(self, buff):
        return self.__dev.write(buff)

    def read(self, max_length, timeout_ms=0):
        return self.__dev.read(max_length, timeout_ms)
