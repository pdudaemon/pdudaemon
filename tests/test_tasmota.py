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
from pdudaemon.drivers.tasmota import GenericTasmota


@pytest.fixture
def pdu():
    return GenericTasmota("dummy", {"ip": "192.0.2.1", "port_count": 2})


@pytest.fixture(name="get_mock")
def fixture_get_mock(mocker):
    return mocker.patch("pdudaemon.drivers.tasmota.requests.get")


@pytest.mark.parametrize("command", ["on", "off"])
def test_port_interaction(pdu, get_mock, command):
    get_mock.return_value.json.return_value = {"POWER2": command.upper()}

    pdu.port_interaction(command, 2)

    get_mock.assert_called_once_with("http://192.0.2.1/cm", {"cmnd": "Power2 %s" % command}, timeout=10)


def test_port_interaction_unexpected_state(pdu, get_mock):
    get_mock.return_value.json.return_value = {"POWER1": "OFF"}

    with pytest.raises(FailedRequestException):
        pdu.port_interaction("on", 1)


@pytest.mark.parametrize("state, expected", [("ON", True), ("OFF", False)])
def test_get_port_state(pdu, get_mock, state, expected):
    get_mock.return_value.json.return_value = {"POWER2": state}

    assert pdu.get_port_state(2) is expected

    get_mock.assert_called_once_with("http://192.0.2.1/cm", {"cmnd": "Power2"}, timeout=10)


def test_get_port_state_credentials(get_mock):
    pdu = GenericTasmota("dummy", {"ip": "192.0.2.1", "username": "user", "password": "pass"})
    get_mock.return_value.json.return_value = {"POWER1": "ON"}

    assert pdu.get_port_state(1) is True

    get_mock.assert_called_once_with(
        "http://192.0.2.1/cm", {"cmnd": "Power1", "user": "user", "password": "pass"}, timeout=10
    )


@pytest.mark.parametrize("response", [{"POWER1": "TOGGLE"}, {"POWER2": "ON"}, {}])
def test_get_port_state_unexpected_response(pdu, get_mock, response):
    get_mock.return_value.json.return_value = response

    with pytest.raises(FailedRequestException):
        pdu.get_port_state(1)


@pytest.mark.parametrize("port", [0, 3])
def test_port_out_of_range(pdu, port):
    with pytest.raises(FailedRequestException):
        pdu.check_port(port)


def test_get_ports(pdu):
    assert pdu.get_ports() == [1, 2]
