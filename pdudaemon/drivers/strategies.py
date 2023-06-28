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

from pdudaemon.drivers.acme import ACME
from pdudaemon.drivers.anelnetpwrctrl import AnelNETPwrCtrlHOME
from pdudaemon.drivers.anelnetpwrctrl import AnelNETPwrCtrlADV
from pdudaemon.drivers.anelnetpwrctrl import AnelNETPwrCtrlIO
from pdudaemon.drivers.anelnetpwrctrl import AnelNETPwrCtrlPRO
from pdudaemon.drivers.apc7900 import APC7900
from pdudaemon.drivers.apc7932 import APC7932
from pdudaemon.drivers.apc7952 import APC7952
from pdudaemon.drivers.apc9218 import APC9218
from pdudaemon.drivers.apc8959 import APC8959
from pdudaemon.drivers.apc9210 import APC9210
from pdudaemon.drivers.apc7920 import APC7920
from pdudaemon.drivers.apc7921 import APC7921
from pdudaemon.drivers.cleware import ClewareUsbSwitch4
from pdudaemon.drivers.conrad197720 import Conrad197720
from pdudaemon.drivers.ubiquity import Ubiquity3Port
from pdudaemon.drivers.ubiquity import Ubiquity6Port
from pdudaemon.drivers.ubiquity import Ubiquity8Port
from pdudaemon.drivers.localcmdline import LocalCmdline
from pdudaemon.drivers.ip9258 import IP9258
from pdudaemon.drivers.sainsmart import Sainsmart
from pdudaemon.drivers.devantech import DevantechETH002
from pdudaemon.drivers.devantech import DevantechETH0621
from pdudaemon.drivers.devantech import DevantechETH484
from pdudaemon.drivers.devantech import DevantechETH008
from pdudaemon.drivers.devantech import DevantechETH8020
from pdudaemon.drivers.devantech import DevantechDS2824
from pdudaemon.drivers.devantechusb import DevantechUSB2
from pdudaemon.drivers.devantechusb import DevantechUSB8
from pdudaemon.drivers.numatousb import NumatoUSB1
from pdudaemon.drivers.numatousb import NumatoUSB2
from pdudaemon.drivers.numatousb import NumatoUSB4
from pdudaemon.drivers.numatousb import NumatoUSB8
from pdudaemon.drivers.numatousb import NumatoUSB16
from pdudaemon.drivers.numatousb import NumatoUSB32
from pdudaemon.drivers.numatousb import NumatoUSB64
from pdudaemon.drivers.servertechpro2 import ServerTechPro2
from pdudaemon.drivers.synaccess import SynNetBooter
from pdudaemon.drivers.tasmota import SonoffS20Tasmota
from pdudaemon.drivers.tasmota import BrennenstuhlWSPL01Tasmota
from pdudaemon.drivers.egpms import EgPMS
from pdudaemon.drivers.ykush import YkushXS
from pdudaemon.drivers.ykush import Ykush
from pdudaemon.drivers.snmp import SNMP
from pdudaemon.drivers.energenieusb import EnerGenieUSB
from pdudaemon.drivers.bcu import BCU
from pdudaemon.drivers.vusbhid import VUSBHID
from pdudaemon.drivers.tplink import TPLink
from pdudaemon.drivers.ip9850 import ip9850
from pdudaemon.drivers.intellinet import Intellinet
from pdudaemon.drivers.esphome import ESPHomeHTTP
from pdudaemon.drivers.servo import Servo
from pdudaemon.drivers.ipower import LindyIPowerClassic8
from pdudaemon.drivers.modbustcp import ModBusTCP
from pdudaemon.drivers.gude1202 import Gude1202
from pdudaemon.drivers.netio4 import Netio4

__all__ = [
    ACME.__name__,
    AnelNETPwrCtrlHOME.__name__,
    AnelNETPwrCtrlADV.__name__,
    AnelNETPwrCtrlIO.__name__,
    AnelNETPwrCtrlPRO.__name__,
    APC7900.__name__,
    APC7932.__name__,
    APC7952.__name__,
    APC9218.__name__,
    APC8959.__name__,
    APC9210.__name__,
    APC7920.__name__,
    APC7921.__name__,
    ClewareUsbSwitch4.__name__,
    Conrad197720.__name__,
    Ubiquity3Port.__name__,
    Ubiquity6Port.__name__,
    Ubiquity8Port.__name__,
    LocalCmdline.__name__,
    IP9258.__name__,
    Sainsmart.__name__,
    DevantechETH002.__name__,
    DevantechETH0621.__name__,
    DevantechETH484.__name__,
    DevantechETH008.__name__,
    DevantechETH8020.__name__,
    DevantechDS2824.__name__,
    DevantechUSB2.__name__,
    DevantechUSB8.__name__,
    NumatoUSB1.__name__,
    NumatoUSB2.__name__,
    NumatoUSB4.__name__,
    NumatoUSB8.__name__,
    NumatoUSB16.__name__,
    NumatoUSB32.__name__,
    NumatoUSB64.__name__,
    ServerTechPro2.__name__,
    SynNetBooter.__name__,
    SonoffS20Tasmota.__name__,
    BrennenstuhlWSPL01Tasmota.__name__,
    EgPMS.__name__,
    YkushXS.__name__,
    Ykush.__name__,
    SNMP.__name__,
    EnerGenieUSB.__name__,
    BCU.__name__,
    VUSBHID.__name__,
    TPLink.__name__,
    ip9850.__name__,
    Intellinet.__name__,
    ESPHomeHTTP.__name__,
    Servo.__name__,
    LindyIPowerClassic8.__name__,
    ModBusTCP.__name__,
    Gude1202.__name__,
    Netio4.__name__,
]
