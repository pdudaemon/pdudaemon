#!/usr/bin/python3

#  Copyright (C) 2026 Qualcomm Technologies, Inc. and/or its subsidiaries.
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

import pytest
from pdudaemon.drivers.devantechusb import DevantechUSB4
from pdudaemon.drivers.driver import FailedRequestException


@pytest.fixture
def pdu():
    return DevantechUSB4("dummy", {"device": "/dev/ttyACM1"})


@pytest.fixture(name="serial_mock")
def fixture_serial_mock(mocker):
    return mocker.patch("pdudaemon.drivers.devantechusb.serial.serial_for_url")


@pytest.mark.parametrize(
    "port, expected", [(1, True), (2, False), (3, True), (4, False), ("3", True)]
)
def test_get_port_state(pdu, serial_mock, port, expected):
    s = serial_mock.return_value
    s.read.return_value = bytes([0b0101])

    assert pdu.get_port_state(port) is expected

    serial_mock.assert_called_once_with("/dev/ttyACM1", 9600, timeout=1, write_timeout=1)
    s.write.assert_called_once_with([0x5B])
    s.read.assert_called_once_with(1)
    s.close.assert_called_once_with()


@pytest.mark.parametrize("port", [0, 5])
def test_get_port_state_port_out_of_range(pdu, serial_mock, port):
    with pytest.raises(RuntimeError, match="range 1 - 4"):
        pdu.get_port_state(port)

    serial_mock.assert_not_called()


def test_get_port_state_no_reply(pdu, serial_mock):
    s = serial_mock.return_value
    s.read.return_value = b""

    with pytest.raises(FailedRequestException, match="No reply"):
        pdu.get_port_state(1)

    s.close.assert_called_once_with()
