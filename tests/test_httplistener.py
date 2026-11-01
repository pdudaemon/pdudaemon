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

import socket
from types import SimpleNamespace

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer
from pdudaemon.httplistener import HTTPListener
from pdudaemon.pdurunner import PDURunner


CONFIG = {
    "daemon": {"hostname": "localhost"},
    "pdus": {
        "pdu1": {"driver": "localcmdline"},
        "pdu2": {"driver": "localcmdline"},
    },
    "aliases": {
        "board": {"hostname": "pdu2", "port": 4},
        "missing": {"hostname": "nopdu", "port": 1},
    },
}


WARNING = "Ports unknown, set port_count or port_names in the driver or config"


@pytest.fixture
def daemon():
    runners = {name: PDURunner(conf, name, 1, 0) for name, conf in CONFIG["pdus"].items()}
    return SimpleNamespace(runners=runners)


@pytest_asyncio.fixture
async def client(daemon):
    listener = HTTPListener(CONFIG, daemon)
    async with TestClient(TestServer(listener.app)) as client:
        yield client


@pytest_asyncio.fixture
async def ui_client(daemon):
    config = {**CONFIG, "daemon": {**CONFIG["daemon"], "web_ui": True}}
    listener = HTTPListener(config, daemon)
    async with TestClient(TestServer(listener.app)) as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/power/status", "/power/status/json"])
async def test_status(client, daemon, path):
    daemon.runners["pdu1"]._set_cached_port_state(1, True)
    daemon.runners["pdu1"]._set_cached_port_state(2, False)

    resp = await client.get(path)

    assert resp.status == 200
    assert await resp.json() == {
        "pdu1": {"driver": "localcmdline", "get_port_state": False, "ports": {"1": {"state": "on"}, "2": {"state": "off"}}, "warning": WARNING},
        "pdu2": {"driver": "localcmdline", "get_port_state": False, "ports": {"4": {"state": "unknown", "alias": "board"}}, "warning": WARNING},
    }


@pytest.mark.asyncio
async def test_status_alias_with_known_state(client, daemon):
    daemon.runners["pdu2"]._set_cached_port_state(4, True)

    resp = await client.get("/power/status")

    assert await resp.json() == {
        "pdu1": {"driver": "localcmdline", "get_port_state": False, "ports": {}, "warning": WARNING},
        "pdu2": {"driver": "localcmdline", "get_port_state": False, "ports": {"4": {"state": "on", "alias": "board"}}, "warning": WARNING},
    }


@pytest.mark.asyncio
async def test_status_driver_ports(client, daemon, mocker):
    mocker.patch.object(daemon.runners["pdu2"].driver, "get_ports", return_value=[1, 4])
    daemon.runners["pdu2"]._set_cached_port_state(1, False)

    resp = await client.get("/power/status", params={"hostname": "pdu2"})

    assert await resp.json() == {
        "pdu2": {
            "driver": "localcmdline",
            "get_port_state": False,
            "ports": {"1": {"state": "off"}, "4": {"state": "unknown", "alias": "board"}},
        },
    }


@pytest.mark.asyncio
async def test_status_hostname(client, daemon):
    daemon.runners["pdu1"]._set_cached_port_state(1, True)

    resp = await client.get("/power/status", params={"hostname": "pdu1"})
    assert resp.status == 200
    assert await resp.json() == {"pdu1": {"driver": "localcmdline", "get_port_state": False, "ports": {"1": {"state": "on"}}, "warning": WARNING}}

    resp = await client.get("/power/status", params={"hostname": "pdu2"})
    assert await resp.json() == {
        "pdu2": {"driver": "localcmdline", "get_port_state": False, "ports": {"4": {"state": "unknown", "alias": "board"}}, "warning": WARNING},
    }


@pytest.mark.asyncio
async def test_status_hostname_without_ports(client):
    resp = await client.get("/power/status", params={"hostname": "pdu1"})

    assert resp.status == 200
    assert await resp.json() == {"pdu1": {"driver": "localcmdline", "get_port_state": False, "ports": {}, "warning": WARNING}}


@pytest.mark.asyncio
async def test_status_unknown_hostname(client):
    resp = await client.get("/power/status", params={"hostname": "nopdu"})

    assert resp.status == 404


@pytest.mark.asyncio
async def test_info(client):
    resp = await client.get("/power/info")

    assert resp.status == 200
    assert await resp.json() == {"hostname": socket.gethostname()}


@pytest.mark.asyncio
async def test_dashboard(ui_client):
    resp = await ui_client.get("/power/dashboard")

    assert resp.status == 200
    assert resp.content_type == "text/html"
    text = await resp.text()
    assert '"/power/status/json"' in text
    assert '"/power/control/"' in text
    assert '"/power/info"' in text


@pytest.mark.asyncio
async def test_dashboard_hostname(ui_client):
    resp = await ui_client.get("/power/dashboard", params={"hostname": "pdu2"})

    assert resp.status == 200


@pytest.mark.asyncio
async def test_dashboard_unknown_hostname(ui_client):
    resp = await ui_client.get("/power/dashboard", params={"hostname": "nopdu"})

    assert resp.status == 404


@pytest.mark.asyncio
async def test_index(ui_client):
    resp = await ui_client.get("/", allow_redirects=False)

    assert resp.status == 302
    assert resp.headers["Location"] == "/power/dashboard"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/", "/power/dashboard"])
async def test_dashboard_disabled(client, path):
    resp = await client.get(path)

    assert resp.status == 404
