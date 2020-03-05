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
import os
log = logging.getLogger("pdud.drivers")


def get_named_entry_point(group, name):
    import pkg_resources
    eps = list(pkg_resources.iter_entry_points(group, name))
    if len(eps) > 1:
        raise Exception('Multiple entry points for {} under {}'.format(group, name))
    if len(eps) == 0:
        return None
    return eps[0]


class PDUDriver(object):
    connection = None
    hostname = ""

    def __init__(self):
        super(PDUDriver, self).__init__()

    @classmethod
    def select(cls, drivername):
        ep = get_named_entry_point('pdudaemon.driver', drivername)
        if ep:
            # Not clear why a driver would reject the driver
            # it is registered for but check anyway:
            c = ep.load()
            if not c.accepts(drivername):
                raise Exception('pdudaemon.driver entry_point {} did not accept configuration'.format(c))
            return c
        candidates = cls.__subclasses__()  # pylint: disable=no-member
        for subc in cls.__subclasses__():  # pylint: disable=no-member
            candidates = candidates + (subc.__subclasses__())
            for subsubc in subc.__subclasses__():
                candidates = candidates + (subsubc.__subclasses__())
        willing = [c for c in candidates if c.accepts(drivername)]
        if len(willing) == 0:
            log.error("No driver accepted the configuration '%s'", drivername)
            os._exit(1)
        log.debug("%s accepted the request", willing[0])
        return willing[0]

    def handle(self, request, port_number):
        log.debug("Driving PDU hostname: %s "
                  "PORT: %s REQUEST: %s",
                  self.hostname, port_number, request)
        if request == "on":
            self.port_on(port_number)
        elif request == "off":
            self.port_off(port_number)
        else:
            log.debug("Unknown request to handle - oops")
            raise UnknownCommandException(
                "Driver doesn't know how to %s " % request
            )
        self._cleanup()

    def port_on(self, port_number):
        self.port_interaction("on", port_number)

    def port_off(self, port_number):
        self.port_interaction("off", port_number)

    def port_interaction(self, command, port_number):
        pass

    def _bombout(self):
        pass

    def _cleanup(self):
        pass


class UnknownCommandException(Exception):
    pass


class FailedRequestException(Exception):
    pass
