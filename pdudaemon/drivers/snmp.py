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
        objecttype = ObjectType(
            ObjectIdentity(self.mib,
                           self.controlpoint,
                           port_number
                           ).addAsn1MibSource(
                'http://mibs.snmplabs.com/asn1/@mib@'), int(set_bit))

        if self.version == 'snmpv3':
            if not self.username:
                raise FailedRequestException("No username set for snmpv3")
            userdata = UsmUserData(self.username, self.authpass, self.privpass)
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
