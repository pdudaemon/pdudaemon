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
from pdudaemon.drivers.driver import FailedRequestException
from pdudaemon.drivers.uhubctl import UHubCtl

STATUS = (
    "Current status for hub 1-1 [2109:2817 VIA Labs, Inc. USB2.0 Hub, USB 2.10, 4 ports, ppps]\n"
    "  Port 1: 0503 power highspeed enable connect [0bda:8153 Realtek USB 10/100/1000 LAN]\n"
    "  Port 2: 0000 off\n"
)


@pytest.fixture
def pdu(mocker):
    mocker.patch("pdudaemon.drivers.uhubctl.which", return_value="/usr/sbin/uhubctl")
    return UHubCtl("dummy", {"location": "1-1"})


@pytest.fixture(name="check_output_mock")
def fixture_check_output_mock(mocker):
    return mocker.patch("pdudaemon.drivers.uhubctl.check_output", return_value=STATUS)


@pytest.mark.parametrize("port, expected", [(1, True), (2, False), ("2", False)])
def test_get_port_state(pdu, check_output_mock, port, expected):
    assert pdu.get_port_state(port) is expected

    check_output_mock.assert_called_once_with(
        ["/usr/sbin/uhubctl", "--location", "1-1", "--port", str(port)], text=True
    )


def test_get_port_state_port_not_reported(pdu, check_output_mock):
    with pytest.raises(FailedRequestException, match="did not report status for port 3"):
        pdu.get_port_state(3)


def test_get_port_state_multiple_hubs(pdu, check_output_mock):
    # e.g. the USB2 and USB3 halves of the same hub
    check_output_mock.return_value = STATUS + (
        "Current status for hub 2-1 [2109:0817 VIA Labs, Inc. USB3.0 Hub, USB 3.10, 4 ports, ppps]\n"
        "  Port 1: 02a0 power 5gbps Rx.Detect\n"
        "  Port 2: 0000 off\n"
    )

    with pytest.raises(FailedRequestException, match="more than one hub"):
        pdu.get_port_state(1)


def test_get_port_state_invalid_port(pdu, check_output_mock):
    with pytest.raises(RuntimeError, match="must be an integer"):
        pdu.get_port_state("usb1")

    check_output_mock.assert_not_called()
