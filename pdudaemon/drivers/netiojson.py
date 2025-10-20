#!/usr/bin/python3

#  Copyright (c) 2025 JUMO GmbH & Co. KG # codespell:ignore
#  Author Semin Buljevic <semin.buljevic@jumo.net> # codespell:ignore
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

import json
import requests
import logging
import os
from pdudaemon.drivers.driver import PDUDriver, FailedRequestException, UnknownCommandException

log = logging.getLogger('pdud.drivers.' + os.path.basename(__file__))


class NetioJson(PDUDriver):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.settings = settings
        self.ip = settings.get('ip', self.hostname)
        self.port = settings.get('port', 80)
        self.username = settings.get('username', 'admin')
        self.password = settings.get('password', 'admin')
        self.number_of_outputs = settings.get('number_of_outputs', 4)
        super(NetioJson, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        return drivername == 'netiojson'

    def port_interaction(self, command, port_number):

        if not 1 <= int(port_number) <= int(self.number_of_outputs):
            raise RuntimeError(f'Requested port no. {port_number} is out of range.')

        url = f'http://{self.username}:{self.password}@{self.ip}:{self.port}/netio.json'
        log.debug(f'Calling API URL: {url}')

        if command == 'on':
            self._do_request(url, port_number, action=1)
        elif command == 'off':
            self._do_request(url, port_number, action=0)
        else:
            raise UnknownCommandException(f'Unknown command: {command}')

    def _do_request(self, url, port_number, action):
        response = requests.post(url, json=self._get_request_json(port_number, action))

        if not self._is_request_successful(response, port_number, action):
            raise FailedRequestException(f'Request failed. Received following response:\n{response.text}')

    def _get_request_json(self, port_number, action):
        data = f'{{"Outputs":[{{"ID":{port_number},"Action":{action}}}]}}'
        return json.loads(data)

    def _is_request_successful(self, response, port_number, action):
        if response.ok:
            output_states = response.json()['Outputs']
            for output_state in output_states:
                if int(output_state['ID']) == int(port_number):
                    return action == output_state['State']
        return False
