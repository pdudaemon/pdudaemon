#!/usr/bin/python3

#  Copyright 2018 Matt Hart <matt@mattface.org>
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
from pysnmp.hlapi import setCmd, SnmpEngine, UsmUserData, UdpTransportTarget, ContextData, CommunityData, ObjectType, ObjectIdentity
import pysnmp.hlapi as pysnmp_api
from pdudaemon.drivers.driver import PDUDriver, FailedRequestException, UnknownCommandException
import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class SNMP(PDUDriver):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        self.version = settings['driver']
        self.mib = settings['mib']
        self.authpass = settings.get('authpassphrase', None)
        self.privpass = settings.get('privpassphrase', None)
        self.community = settings.get('community', None)
        self.controlpoint = settings['controlpoint']
        self.username = settings.get('username', None)
        self.onsetting = settings['onsetting']
        self.offsetting = settings['offsetting']
        self.inside_number = settings.get('inside_number', None)
        self.static_ending = settings.get('static_ending', None)
        self.auth_protocol = settings.get('auth_protocol', None)
        self.priv_protocol = settings.get('priv_protocol', None)
        super(SNMP, self).__init__()

    @classmethod
    def accepts(cls, drivername):
        if drivername in ['snmpv3', 'snmpv1']:
            return True
        return False

    def validate(self):
        pass

    def port_interaction(self, command, port_number):
        if command == "on":
            set_bit = self.onsetting
        elif command == "off":
            set_bit = self.offsetting
        else:
            raise UnknownCommandException("Unknown command %s." % (command))

        transport = UdpTransportTarget((self.hostname, 161))

        if self.inside_number:
            # It is possible to pass 2 or 3 snmp argument values
            filled_controlpoint = self.controlpoint.replace('*', str(port_number))
            indexed_object_list = [self.mib, filled_controlpoint]
            # If there is a key static_ending available, add a static ending value
            if self.static_ending is not None:
                indexed_object_list.append(int(self.static_ending))
        else:
            indexed_object_list = [self.mib, self.controlpoint, port_number]

        objecttype = ObjectType(
            ObjectIdentity(*indexed_object_list).addAsn1MibSource(
                'http://mibs.snmplabs.com/asn1/@mib@'), int(set_bit))

        if self.version == 'snmpv3':
            if not self.username:
                raise FailedRequestException("No username set for snmpv3")

            protocols = {}
            if self.auth_protocol is not None:
                a_protocol = getattr(pysnmp_api, self.auth_protocol)
                protocols['authProtocol'] = a_protocol

            if self.priv_protocol is not None:
                p_protocol = getattr(pysnmp_api, self.priv_protocol)
                protocols['privProtocol'] = p_protocol

            userdata = UsmUserData(self.username, self.authpass, self.privpass, **protocols)
            errorIndication, errorStatus, errorIndex, varBinds = next(
                setCmd(SnmpEngine(),
                       userdata,
                       transport,
                       ContextData(),
                       objecttype)
            )
        elif self.version == 'snmpv1':
            if not self.community:
                raise FailedRequestException("No community set for snmpv1")
            errorIndication, errorStatus, errorIndex, varBinds = next(
                setCmd(SnmpEngine(),
                       CommunityData(self.community),
                       transport,
                       ContextData(),
                       objecttype)
            )
        else:
            raise FailedRequestException("Unknown snmp version")

        if errorIndication:
            raise FailedRequestException(errorIndication)
        elif errorStatus:
            raise FailedRequestException(errorStatus)
        else:
            for varBind in varBinds:
                log.debug(' = '.join([x.prettyPrint() for x in varBind]))
            return True
