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

from lavapdu.drivers.acme import ACME  # pylint: disable=W0611
from lavapdu.drivers.apc7932 import APC7932  # pylint: disable=W0611
from lavapdu.drivers.apc7952 import APC7952  # pylint: disable=W0611
from lavapdu.drivers.apc9218 import APC9218  # pylint: disable=W0611
from lavapdu.drivers.apc8959 import APC8959  # pylint: disable=W0611
from lavapdu.drivers.apc9210 import APC9210  # pylint: disable=W0611
from lavapdu.drivers.apc7921 import APC7921  # pylint: disable=W0611
from lavapdu.drivers.ubiquity import Ubiquity3Port  # pylint: disable=W0611
from lavapdu.drivers.ubiquity import Ubiquity6Port  # pylint: disable=W0611
from lavapdu.drivers.localcmdline import LocalCmdline
from lavapdu.drivers.ip9258 import IP9258
from lavapdu.drivers.sainsmart import Sainsmart
from lavapdu.drivers.devantech import DevantechETH002
from lavapdu.drivers.devantech import DevantechETH0621
from lavapdu.drivers.devantech import DevantechETH484
from lavapdu.drivers.devantech import DevantechETH008
from lavapdu.drivers.devantech import DevantechETH8020

assert ACME
assert APC7932
assert APC7952
assert APC9218
assert APC8959
assert APC9210
assert APC7921
assert Ubiquity3Port
assert Ubiquity6Port
assert IP9258
assert Sainsmart
assert DevantechETH002
assert DevantechETH0621
assert DevantechETH484
assert DevantechETH008
assert DevantechETH8020
