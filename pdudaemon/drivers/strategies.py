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

from pdudaemon.drivers.acme import ACME  # pylint: disable=W0611
from pdudaemon.drivers.apc7932 import APC7932  # pylint: disable=W0611
from pdudaemon.drivers.apc7952 import APC7952  # pylint: disable=W0611
from pdudaemon.drivers.apc9218 import APC9218  # pylint: disable=W0611
from pdudaemon.drivers.apc8959 import APC8959  # pylint: disable=W0611
from pdudaemon.drivers.apc9210 import APC9210  # pylint: disable=W0611
from pdudaemon.drivers.apc7921 import APC7921  # pylint: disable=W0611
from pdudaemon.drivers.ubiquity import Ubiquity3Port  # pylint: disable=W0611
from pdudaemon.drivers.ubiquity import Ubiquity6Port  # pylint: disable=W0611
from pdudaemon.drivers.localcmdline import LocalCmdline
from pdudaemon.drivers.ip9258 import IP9258
from pdudaemon.drivers.sainsmart import Sainsmart
from pdudaemon.drivers.devantech import DevantechETH002
from pdudaemon.drivers.devantech import DevantechETH0621
from pdudaemon.drivers.devantech import DevantechETH484
from pdudaemon.drivers.devantech import DevantechETH008
from pdudaemon.drivers.devantech import DevantechETH8020
from pdudaemon.drivers.devantechusb import DevantechUSB2
from pdudaemon.drivers.devantechusb import DevantechUSB8
from pdudaemon.drivers.synaccess import SynNetBooter
from pdudaemon.drivers.egpms import EgPMS

assert ACME
assert APC7932
assert APC7952
assert APC9218
assert APC8959
assert APC9210
assert APC7921
assert EgPMS
assert Ubiquity3Port
assert Ubiquity6Port
assert IP9258
assert Sainsmart
assert DevantechETH002
assert DevantechETH0621
assert DevantechETH484
assert DevantechETH008
assert DevantechETH8020
assert DevantechUSB2
assert DevantechUSB8
assert SynNetBooter
