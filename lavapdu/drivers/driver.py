#! /usr/bin/python

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


class PDUDriver(object):
    connection = None
    hostname = ""

    def __init__(self):
        super(PDUDriver, self).__init__()

    @classmethod
    def select(cls, drivername):
        logging.debug("adding PDUDriver subclasses: %s" % cls.__subclasses__())
        candidates = cls.__subclasses__()  # pylint: disable=no-member
        for subc in cls.__subclasses__():
            logging.debug("adding %s subclasses: %s" % (subc,subc.__subclasses__()))
            candidates = candidates + (subc.__subclasses__())
            for subsubc in subc.__subclasses__():
                logging.debug("adding %s subclasses: %s" % (subsubc,subsubc.__subclasses__()))
                candidates = candidates + (subsubc.__subclasses__())
        logging.debug(candidates)
        willing = [c for c in candidates if c.accepts(drivername)]
        if len(willing) == 0:
            raise NotImplementedError(
                "No driver accepted the request "
                "'%s' with the specified job parameters. %s" % (drivername, cls)
            )
        logging.debug("%s accepted the request" % willing[0])
        return willing[0]

    def handle(self, request, port_number, delay=0):
        logging.debug("Driving PDU hostname: %s PORT: %s REQUEST: %s (delay %s)" %(self.hostname,port_number,request,delay))
        if request == "on":
            self.port_on(port_number)
        elif request == "off":
            self.port_off(port_number)
        else:
            logging.debug("Unknown request to handle - oops")
            raise NotImplementedError(
                "Driver doesn't know how to %s " % (request)
            )
        self._cleanup()

    #def _port_interaction(self, command, port_number):
    #    super(PDUDriver, self).port_interaction(command,port_number)

    def port_on(self, port_number):
        self.port_interaction("on", port_number)

    def port_off(self, port_number):
        self.port_interaction("off", port_number)