#!/usr/bin/python3

#  Copyright 2016 Quentin Schulz <quentin.schulz@free-electrons.com>
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
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class DevantechBase(PDUDriver):
    connection = None
    port_count = 0

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.ip = settings["ip"]
        self.port = settings.get("port", 17494)
        self.password = settings.get("password")
        super(DevantechBase, self).__init__()

    def connect(self):
        self.connection = socket.create_connection((self.ip, self.port))
        if self.password:
            log.debug("Attempting connection to %s:%s with provided password.", self.hostname, self.port)
            msg = '\x79' + self.password
            ret = self.connection.sendall(msg)
            if ret:
                log.error("Failed to send message.")
                raise RuntimeError("Failed to send message.")
            ret = self.connection.recv(1)
            if ret != '\x01':
                log.error("Authentication failed.")
                raise RuntimeError("Failed to authenticate. Verify your password.")

    def port_interaction(self, command, port_number):
        self.connect()
        if port_number > self.port_count:
            log.error("There are only %d ports. Provide a port number lesser than %d." % (self.port_count, self.port_count))
            raise RuntimeError("There are only %d ports. Provide a port number lesser than %d." % (self.port_count, self.port_count))

        if command == "on":
            msg = '\x20'
        elif command == "off":
            msg = '\x21'
        else:
            log.error("Unknown command %s." % (command))
            return
        msg += chr(port_number)
        msg += '\x00'
        log.debug("Attempting control: %s port: %d hostname: %s." % (command, port_number, self.hostname))
        ret = self.connection.sendall(msg)
        if ret:
            log.error("Failed to send message.")
            raise RuntimeError("Failed to send message.")
        ret = self.connection.recv(1)
        if ret != '\x00':
            log.error("Failed to send %s command on port %d of %s." % (command, port_number, self.hostname))
            raise RuntimeError("Failed to send %s command on port %d of %s." % (command, port_number, self.hostname))

    def _close_connection(self):
        # Logout
        log.debug("Closing connection.")
        if self.password:
            log.debug("Attempting to logout.")
            ret = self.connection.sendall('\x7B')
            if ret:
                log.error("Failed to send message.")
                raise RuntimeError("Failed to send message.")
            ret = self.connection.recv(1)
            if ret != '\x00':
                log.error("Failed to logout of %s." % self.hostname)
                raise RuntimeError("Failed to logout of %s." % self.hostname)
        self.connection.close()

    def _cleanup(self):
        self._close_connection()

    def _bombout(self):
        self._close_connection()

    @classmethod
    def accepts(cls, drivername):
        return False


class DevantechETH002(DevantechBase):
    port_count = 2

    @classmethod
    def accepts(cls, drivername):
        if drivername == "devantech_eth002":
            return True
        return False


class DevantechETH0621(DevantechBase):
    port_count = 2

    @classmethod
    def accepts(cls, drivername):
        if drivername == "devantech_eth0621":
            return True
        return False


class DevantechETH484(DevantechBase):
    port_count = 4

    @classmethod
    def accepts(cls, drivername):
        if drivername == "devantech_eth484":
            return True
        return False


class DevantechETH008(DevantechBase):
    port_count = 8

    @classmethod
    def accepts(cls, drivername):
        if drivername == "devantech_eth008":
            return True
        return False


class DevantechETH8020(DevantechBase):
    port_count = 20

    @classmethod
    def accepts(cls, drivername):
        if drivername == "devantech_eth8020":
            return True
        return False
