#!/usr/bin/python3

#  Copyright 2015 Alexander Couzens <lynxis@fe80.eu>
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
from paramiko import SSHClient
from paramiko.ssh_exception import SSHException
from paramiko import RejectPolicy, WarningPolicy
from pdudaemon.drivers.driver import PDUDriver
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class UbiquityBase(PDUDriver):
    client = None
    # overwrite power_count
    port_count = 0

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings

        self.sshport = 22
        self.username = "ubnt"
        self.password = "ubnt"

        # verify ssh hostkey? unknown hostkey will make this job fail
        self.verify_hostkey = True

        if "sshport" in settings:
            self.sshport = settings["sshport"]
        if "username" in settings:
            self.username = settings["username"]
        if "password" in settings:
            self.password = settings["password"]
        if "verify_hostkey" in settings:
            self.verify_hostkey = settings["verify_hostkey"]

        super(UbiquityBase, self).__init__()

    def connect(self):
        log.info("Connecting to Ubiquity mfi %s@%s:%d",
                 self.username, self.hostname, self.sshport)
        self.client = SSHClient()
        self.client.load_system_host_keys()

        if self.verify_hostkey:
            self.client.set_missing_host_key_policy(RejectPolicy())
        else:
            self.client.set_missing_host_key_policy(WarningPolicy())

        self.client.connect(hostname=self.hostname, port=self.sshport,
                            username=self.username, password=self.password)

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        log.debug("Running port_interaction from UbiquityBase")
        self.connect()
        if port_number > self.port_count:
            raise RuntimeError("We only have ports 1 - %d. %d > maxPorts (%d)"
                               % self.port_count, port_number, self.port_count)

        if command == "on":
            command = "sh -c 'echo 1 > /proc/power/relay%d'" % port_number
        elif command == "off":
            command = "sh -c 'echo 0 > /proc/power/relay%d'" % port_number

        try:
            stdin, stdout, stderr = self.client.exec_command(command,
                                                             bufsize=-1,
                                                             timeout=3)
            stdin.close()
        except SSHException:
            pass

    def _cleanup(self):
        self.client.close()

    def _bombout(self):
        self.client.close()

    @classmethod
    def accepts(cls, drivername):
        return False


class Ubiquity3Port(UbiquityBase):
    port_count = 3

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ubntmfi3port":
            return True
        return False


class Ubiquity6Port(UbiquityBase):
    port_count = 6

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ubntmfi6port":
            return True
        return False


class Ubiquity8Port(UbiquityBase):
    port_count = 8

    @classmethod
    def accepts(cls, drivername):
        if drivername == "ubntmfi8port":
            return True
        return False
