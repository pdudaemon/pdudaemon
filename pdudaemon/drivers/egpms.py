#!/usr/bin/python3

#  Copyright 2017 Sjoerd Simons Schulz <sjoerd.simons@collabora.co.uk>
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
from pdudaemon.drivers.driver import PDUDriver
import socket
from array import array

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class EgPMS(PDUDriver):
    port_count = 4

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.ip = settings["ip"]
        self.password = array('B', settings["password"].encode("utf-8") + 8 * b' ')[:8]
        self.challenge = None

    def authresponse(self, part):
        response = self.challenge[part] ^ self.password[part + 2]
        response *= self.password[part]
        response ^= self.password[part + 4] << 8 | self.password[part + 6]
        response ^= self.challenge[part + 2]

        r = array('B', [response & 0xff, (response >> 8) & 0xff])
        return r

    def encode_state(self, status):
        state = status ^ self.challenge[2]
        state += self.challenge[3]
        state ^= self.password[0]
        state += self.password[1]

        return state & 0xff

    def decode_state(self, state):
        state = state - self.password[1]
        state ^= self.password[0]
        state -= self.challenge[3]
        state ^= self.challenge[2]

        return state & 0xff

    def dump_status(self, status):
        status.reverse()
        for b in status:
            s = self.decode_state(b)
            log.debug("on: %d (raw: %x)" % (s >> 4 == 1, s))

    def connect(self):
        self.socket = socket.create_connection((self.ip, 5000))
        self.socket.send(b'\x11')
        self.challenge = array('B', self.socket.recv(4))

        self.socket.send(self.authresponse(0) + self.authresponse(1))
        status = array('B', self.socket.recv(self.port_count))
        log.debug("Connected")
        self.dump_status(status)

    def disconnect(self):
        # From egctl:
        # Empirically found way to close session w/o 4 second timeout on
        # the device side is to send some invalid sequence. This helps
        # to avoid a hiccup on subsequent run of the utility.
        #
        # Other protocol documents explain that after the current settings the
        # device waits for a schedule update for a while (if any) but will go
        # back to the start state if it doesn't make sense.
        self.socket.send(b'\x11')
        self.socket.close()

    def port_interaction(self, command, port_number):
        SWITCH_ON = 0x1
        SWITCH_OFF = 0x2
        DONT_SWITCH = 0x4
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = "Port should be in the range 1 - %d" % (self.port_count)
            log.error(err)
            raise RuntimeError(err)

        if command == "on":
            on = True
        elif command == "off":
            on = False
        else:
            log.error("Unknown command %s." % (command))
            return

        self.connect()
        log.debug("Attempting control: {} port: {} hostname: {}.".format(command, port_number, self.hostname))
        update = array('B')
        for s in range(1, self.port_count + 1):
            if s != port_number:
                update.append(self.encode_state(DONT_SWITCH))
            else:
                update.append(
                    self.encode_state(SWITCH_ON if on else SWITCH_OFF))

        # States get send in reverse port order bytewise
        update.reverse()

        self.socket.send(update)
        status = array('B', self.socket.recv(self.port_count))
        self.disconnect()

        log.debug("Updated")
        self.dump_status(status)

    @classmethod
    def accepts(cls, drivername):
        if drivername == 'egpms':
            return True
        return False
