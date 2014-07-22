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

import pexpect
import os
import logging
import pkgutil
import sys


class PDUEngine():
    connection = None
    prompt = 0
    driver = None
    firmware_dict = {}

    def __init__(self, pdu_hostname):
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    pe = PDUEngine("pdu01")
    pe.driver.port_off(1)
    pe.driver.port_on(1)
    pe.close()
    pe = PDUEngine("pdu03")
    pe.driver.port_off(3)
    pe.driver.port_on(3)
    pe.close()

    #pe = PDUEngine("pdu16")
    #pe.close()