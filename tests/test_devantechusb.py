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
from pdudaemon.drivers.devantechusb import (
    DevantechUSB2,
    DevantechUSB4,
    DevantechUSB6,
    DevantechUSB8,
)
from pdudaemon.drivers.driver import FailedRequestException


@pytest.fixture
def pdu():
    return DevantechUSB4("dummy", {"device": "/dev/ttyACM1"})


@pytest.fixture(name="serial_mock")
def fixture_serial_mock(mocker):
    return mocker.patch("pdudaemon.drivers.devantechusb.serial.serial_for_url")


@pytest.mark.parametrize(
    "command, port, byte",
    [("on", 1, 0x65), ("on", 4, 0x68), ("off", 1, 0x6F), ("off", 4, 0x72), ("on", "2", 0x66)],
)
def test_port_interaction(pdu, serial_mock, command, port, byte):
    pdu.port_interaction(command, port)

    serial_mock.assert_called_once_with("/dev/ttyACM1", 9600, timeout=1, write_timeout=1)
    s = serial_mock.return_value
    s.write.assert_called_once_with([byte])
    s.close.assert_called_once_with()


def test_port_interaction_unknown_command(pdu, serial_mock):
    pdu.port_interaction("reboot", 1)

    serial_mock.assert_not_called()


@pytest.mark.parametrize("port", [0, 5])
def test_port_interaction_port_out_of_range(pdu, serial_mock, port):
    with pytest.raises(RuntimeError):
        pdu.port_interaction("on", port)

    serial_mock.assert_not_called()


def test_default_device(serial_mock):
    pdu = DevantechUSB4("dummy", {})

    pdu.port_interaction("on", 1)

    serial_mock.assert_called_once_with("/dev/ttyACM0", 9600, timeout=1, write_timeout=1)


@pytest.mark.parametrize(
    "cls, port_count",
    [(DevantechUSB2, 2), (DevantechUSB4, 4), (DevantechUSB6, 6), (DevantechUSB8, 8)],
)
def test_port_count(serial_mock, cls, port_count):
    pdu = cls("dummy", {})

    pdu.port_interaction("on", port_count)
    with pytest.raises(RuntimeError):
        pdu.port_interaction("on", port_count + 1)

    serial_mock.return_value.write.assert_called_once_with([0x64 + port_count])


@pytest.mark.parametrize(
    "cls, drivername",
    [
        (DevantechUSB2, "devantech_USB-RLY02"),
        (DevantechUSB2, "devantech_USB-RLY82"),
        (DevantechUSB4, "devantech_USB-RLY04"),
        (DevantechUSB6, "devantech_USB-RLY06"),
        (DevantechUSB8, "devantech_USB-RLY08B"),
        (DevantechUSB8, "devantech_USB-RLY16"),
        (DevantechUSB8, "devantech_USB-RLY16L"),
        (DevantechUSB8, "devantech_USB-OPTO-RLY88"),
        (DevantechUSB8, "devantech_USB-OPTO-RLY816"),
    ],
)
def test_accepts(cls, drivername):
    assert cls.accepts(drivername)
    for other in (DevantechUSB2, DevantechUSB4, DevantechUSB6, DevantechUSB8):
        if other is not cls:
            assert not other.accepts(drivername)


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
