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
from subprocess import CalledProcessError
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


@pytest.fixture(name="check_call_mock")
def fixture_check_call_mock(mocker):
    return mocker.patch("pdudaemon.drivers.uhubctl.check_call")


@pytest.mark.parametrize("command, port", [("on", 1), ("off", 2), ("on", "3")])
def test_port_interaction(pdu, check_call_mock, command, port):
    pdu.port_interaction(command, port)

    check_call_mock.assert_called_once_with(
        ["/usr/sbin/uhubctl", "--location", "1-1", "--port", str(port), "--action", command]
    )


def test_port_interaction_unknown_command(pdu, check_call_mock):
    pdu.port_interaction("reboot", 1)

    check_call_mock.assert_not_called()


def test_port_interaction_invalid_port(pdu, check_call_mock):
    with pytest.raises(RuntimeError):
        pdu.port_interaction("on", "usb1")

    check_call_mock.assert_not_called()


def test_port_interaction_command_fails(pdu, check_call_mock):
    check_call_mock.side_effect = CalledProcessError(1, "uhubctl")

    with pytest.raises(CalledProcessError):
        pdu.port_interaction("on", 1)


def test_missing_location(mocker):
    mocker.patch("pdudaemon.drivers.uhubctl.which", return_value="/usr/sbin/uhubctl")

    with pytest.raises(RuntimeError):
        UHubCtl("dummy", {})


def test_uhubctl_not_found(mocker):
    mocker.patch("pdudaemon.drivers.uhubctl.which", return_value=None)

    with pytest.raises(RuntimeError):
        UHubCtl("dummy", {"location": "1-1"})


def test_accepts():
    assert UHubCtl.accepts("uhubctl")
    assert not UHubCtl.accepts("localcmdline")


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


def test_get_port_state_command_fails(pdu, check_output_mock):
    check_output_mock.side_effect = CalledProcessError(1, "uhubctl")

    with pytest.raises(CalledProcessError):
        pdu.get_port_state(1)
