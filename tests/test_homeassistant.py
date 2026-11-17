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
from pdudaemon.drivers.driver import FailedRequestException
from pdudaemon.drivers.homeassistant import HomeAssistantHTTP


@pytest.fixture
def pdu():
    return HomeAssistantHTTP("dummy", {"hostname": "192.0.2.1", "port": 8123,
                                       "api_key": "secret"})


@pytest.fixture(name="get_mock")
def fixture_get_mock(mocker):
    return mocker.patch("pdudaemon.drivers.homeassistant.requests.get")


@pytest.fixture(name="post_mock")
def fixture_post_mock(mocker):
    return mocker.patch("pdudaemon.drivers.homeassistant.requests.post")


@pytest.mark.parametrize("command, action", [("on", "turn_on"), ("off", "turn_off")])
def test_port_interaction(pdu, post_mock, command, action):
    pdu.port_interaction(command, "relay1")

    post_mock.assert_called_once_with(
        "http://192.0.2.1:8123/api/services/switch/%s" % action,
        headers={"Authorization": "Bearer secret"},
        json={"entity_id": "switch.relay1"},
    )
    post_mock.return_value.raise_for_status.assert_called_once_with()


def test_port_interaction_unknown_command(pdu, post_mock):
    with pytest.raises(FailedRequestException):
        pdu.port_interaction("reboot", "relay1")

    post_mock.assert_not_called()


def test_port_interaction_http_error(pdu, post_mock):
    post_mock.return_value.raise_for_status.side_effect = requests.HTTPError("401")

    with pytest.raises(requests.HTTPError):
        pdu.port_interaction("on", "relay1")


def test_default_hostname_and_port(post_mock):
    pdu = HomeAssistantHTTP("192.0.2.2", {"api_key": "secret"})

    pdu.port_interaction("on", "relay1")

    post_mock.assert_called_once_with(
        "http://192.0.2.2:80/api/services/switch/turn_on",
        headers={"Authorization": "Bearer secret"},
        json={"entity_id": "switch.relay1"},
    )


def test_accepts():
    assert HomeAssistantHTTP.accepts("home-assistant-http")
    assert not HomeAssistantHTTP.accepts("esphome-http")


@pytest.mark.parametrize("state, expected", [("on", True), ("off", False)])
def test_get_port_state(pdu, get_mock, state, expected):
    get_mock.return_value.json.return_value = {"entity_id": "switch.relay1",
                                               "state": state}

    assert pdu.get_port_state("relay1") is expected

    get_mock.assert_called_once_with(
        "http://192.0.2.1:8123/api/states/switch.relay1",
        headers={"Authorization": "Bearer secret"},
    )


@pytest.mark.parametrize("response", [{"state": "ON"}, {"state": "unavailable"}, {}])
def test_get_port_state_unexpected_response(pdu, get_mock, response):
    get_mock.return_value.json.return_value = response

    with pytest.raises(FailedRequestException, match="Unexpected state"):
        pdu.get_port_state("relay1")


def test_get_port_state_http_error(pdu, get_mock):
    get_mock.return_value.raise_for_status.side_effect = requests.HTTPError("401")

    with pytest.raises(requests.HTTPError):
        pdu.get_port_state("relay1")
