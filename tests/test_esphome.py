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
import requests
from requests.auth import HTTPDigestAuth
from pdudaemon.drivers.esphome import ESPHomeHTTP


@pytest.fixture
def pdu():
    return ESPHomeHTTP("192.0.2.1", {"port": 8080})


@pytest.fixture(name="get_mock")
def fixture_get_mock(mocker):
    return mocker.patch("pdudaemon.drivers.esphome.requests.get")


@pytest.mark.parametrize("state, expected", [("ON", True), ("OFF", False)])
def test_get_port_state(pdu, get_mock, state, expected):
    get_mock.return_value.json.return_value = {"id": "switch-relay1", "state": state}

    assert pdu.get_port_state("relay1") is expected

    get_mock.assert_called_once_with("http://192.0.2.1:8080/switch/relay1", auth=None, timeout=10)


def test_get_port_state_credentials(get_mock):
    pdu = ESPHomeHTTP("192.0.2.1", {"username": "user", "password": "pass"})
    get_mock.return_value.json.return_value = {"state": "ON"}

    assert pdu.get_port_state("relay1") is True

    get_mock.assert_called_once_with(
        "http://192.0.2.1:80/switch/relay1", auth=HTTPDigestAuth("user", "pass"), timeout=10
    )


def test_get_port_state_http_error(pdu, get_mock):
    get_mock.return_value.raise_for_status.side_effect = requests.HTTPError("404")

    with pytest.raises(requests.HTTPError):
        pdu.get_port_state("relay1")
