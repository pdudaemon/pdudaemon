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
from importlib import metadata

log = logging.getLogger("pdud.drivers")


def get_named_entry_point(group, name):
    eps = metadata.entry_points()
    matches = list(eps.select(group=group, name=name))

    if len(matches) > 1:
        raise RuntimeError(f"Multiple entry points for {group} under {name}")

    return matches[0] if matches else None


class PDUDriver(object):
    connection = None
    hostname = ""
    # number of ports of the PDU, numbered from first_port; 0 if the driver
    # doesn't know how many ports the PDU has
    port_count = 0
    # number of the first port of the PDU, 0 or 1
    first_port = 1
    # names of the ports of the PDU, or None to number the ports instead
    port_names = None

    def __init__(self):
        super(PDUDriver, self).__init__()

    def configure_ports(self, settings):
        """Apply the port_count, first_port and port_names PDU settings.
        port_count is only used if the driver doesn't know how many ports the
        PDU has; first_port overrides the driver's.
        """
        if not self.port_count and "port_count" in settings:
            self.port_count = int(settings["port_count"])
        if "first_port" in settings:
            first_port = int(settings["first_port"])
            if first_port not in (0, 1):
                raise ValueError("first_port must be 0 or 1, not {}".format(first_port))
            self.first_port = first_port
        if "port_names" in settings:
            self.port_names = [str(name) for name in settings["port_names"]]

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

    def port_on(self, port):
        self.port_interaction("on", port)

    def port_off(self, port):
        self.port_interaction("off", port)

    def get_port_state(self, port) -> bool:
        """Return True if the port is powered on, False if powered off. Raises
        UnknownCommandException if retrieving the port status is unsupported by
        the driver.
        """
        raise UnknownCommandException("Driver doesn't support get-port-state")

    def supports_get_port_state(self) -> bool:
        """Return True if the driver can retrieve the state of a port with
        get_port_state().
        """
        return type(self).get_port_state is not PDUDriver.get_port_state

    def get_ports(self) -> list:
        """Return the port names or numbers of the PDU, or an empty list if the
        driver doesn't know which ports the PDU has.
        """
        if self.port_names is not None:
            return list(self.port_names)
        return list(range(self.first_port, self.first_port + (self.port_count or 0)))

    def check_port(self, port) -> str:
        """Return the port as a string to pass to the driver. Raises
        FailedRequestException if the port isn't one of the ports of the PDU.
        The port isn't checked if the driver doesn't know which ports the PDU
        has.
        """
        if self.port_names is not None:
            if str(port) not in self.port_names:
                raise FailedRequestException("Port {} is not one of the ports {}".format(
                    port, ", ".join(self.port_names)))
            return str(port)
        if self.port_count:
            last_port = self.first_port + self.port_count - 1
            try:
                number = int(port)
            except ValueError:
                number = None
            if number is None or not self.first_port <= number <= last_port:
                raise FailedRequestException("Port {} is not one of the ports {}..{}".format(
                    port, self.first_port, last_port))
            return str(number)
        return str(port)

    def port_interaction(self, command, port):
        pass

    def _bombout(self):
        pass

    def _cleanup(self):
        pass


class UnknownCommandException(Exception):
    pass


class FailedRequestException(Exception):
    pass
