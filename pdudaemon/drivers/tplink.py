#!/usr/bin/python3

#  Copyright 2020
#  Author Matt Hart <matt@mattface.org>
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
#
#  Confirmed devices
#    - KP303: https://www.tp-link.com/uk/home-networking/smart-plug/kp303/
#    - KP105: https://www.tp-link.com/uk/home-networking/smart-plug/kp105/
#    - HS105: https://www.tp-link.com/us/home-networking/smart-plug/hs105/

import logging
import json
import socket
from pdudaemon.drivers.driver import PDUDriver
from struct import pack
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class TPLink(PDUDriver):
    connection = None

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.childinfo = {}
        self.getinfo()
        super(TPLink, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        if drivername == "tplink":
            return True
        return False

    def encrypt(self, string):
        key = 171
        result = pack(">I", len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result

    def decrypt(self, string):
        key = 171
        result = ""
        for i in string:
            a = key ^ i
            key = i
            result += chr(a)
        return result

    def getinfo(self):
        datadict = {
            'system': {
                'get_sysinfo': {
                }
            }
        }
        res = self.send_command(json.dumps(datadict))
        if res:
            resdict = json.loads(res)
            self.childinfo = resdict.get("system", {}).get("get_sysinfo", {}).get("children", {})

    def send_command(self, json_string):
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.hostname, 9999))
            sock_tcp.settimeout(None)
            sock_tcp.send(self.encrypt(json_string))
            data = sock_tcp.recv(2048)
            sock_tcp.close()
            decrypted = self.decrypt(data[4:])
            return (decrypted)
        except socket.error:
            log.error(f"Could not connect to host {self.hostname}:9999")

    def get_context(self, port_number):
        for child in self.childinfo:
            child_port = (int(child['alias'].split("_")[-1]) + 1)
            if int(port_number) == int(child_port):
                return ({"child_ids": [child["id"]]})
        return ({})

    def port_interaction(self, command, port_number):
        state = 0
        context = None
        if command == "on":
            state = 1
        if self.childinfo:
            if int(port_number) > len(self.childinfo):
                return (False)
            context = self.get_context(port_number)
        datadict = {
            'context': context,
            'system': {
                'set_relay_state': {
                    'state': state,
                }
            }
        }
        log.debug(datadict)
        self.send_command(json.dumps(datadict))
