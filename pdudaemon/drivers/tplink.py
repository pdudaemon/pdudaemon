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
        self.device_id = None
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

            # self.childinfo is empty for single plug outlets (self.childinfo == {})
            self.childinfo = resdict.get("system", {}).get("get_sysinfo", {}).get("children", {})
            self.device_id = resdict.get("system", {}).get("get_sysinfo", {})['deviceId']

            log.debug("TP-Link outlet device info:")
            log.debug(resdict)
        else:
            log.error("Failed to get TP-Link outlet device info!")

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
        for i, child in enumerate(self.childinfo, start=1):
            try:
                port_id = str(child['id'])
                log.debug(f"child ID is {port_id}")

                # If the port_id contains the device id,
                if port_id.find(self.device_id) == 0:
                    # Get the substring that comes after the device_id
                    # in the port_id. This corresponds to the outlet number
                    child_port = int(port_id[len(self.device_id)-1:])

                    # Add 1 because outlet numbers are 0 based
                    child_port = child_port + 1

                if port_number == int(child_port):
                    return ({"child_ids": [port_id]})
            except:
                logging.exception("Oulet device/outlet id issue")
                # If the device id method above doesn't work for some reason,
                # fall back to just counting outlets in the list.
                if i == int(port_number):
                    return ({"child_ids": [port_id]})

        # Outlet is a single plug, there are no childinfo's
        return ({})

    def is_integer(self, n):
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

    def port_interaction(self, command, port_number):
        state = 0
        context = None

        # Ensure that port_number is an integer
        if not self.is_integer(port_number):
            log.error("Expected port value to be an integer!")
            return (False)

        if command == "on":
            log.debug("Commanding outlet to turn on")
            state = 1
        else:
            log.debug("Commanding outlet to turn off")

        if self.childinfo:
            if int(port_number) > len(self.childinfo):
                log.error(f"Outlet number '{port_number}' is larger the the maximum number of outlets on device which is '{len(self.childinfo)}'")
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

        log.debug("Sending the following json command:")
        log.debug(datadict)

        res = self.send_command(json.dumps(datadict))
        if not res:
            return (False)

        return (True)
