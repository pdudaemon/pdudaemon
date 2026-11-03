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
from pdudaemon.drivers.homeassistant import HomeAssistantHTTP


@pytest.fixture
def pdu():
    return HomeAssistantHTTP("dummy", {"hostname": "192.0.2.1", "port": 8123,
                                       "api_key": "secret"})


@pytest.fixture(name="get_mock")
def fixture_get_mock(mocker):
    return mocker.patch("pdudaemon.drivers.homeassistant.requests.get")


@pytest.mark.parametrize(
    "state, expected", [("on", True), ("off", False), ("unavailable", False)]
)
def test_get_port_state(pdu, get_mock, state, expected):
    get_mock.return_value.json.return_value = {"entity_id": "switch.relay1",
                                               "state": state}

    assert pdu.get_port_state("relay1") is expected

    get_mock.assert_called_once_with(
        "http://192.0.2.1:8123/api/states/switch.relay1",
        headers={"Authorization": "Bearer secret"},
        timeout=10,
    )


def test_get_port_state_http_error(pdu, get_mock):
    get_mock.return_value.raise_for_status.side_effect = requests.HTTPError("401")

    with pytest.raises(requests.HTTPError):
        pdu.get_port_state("relay1")
