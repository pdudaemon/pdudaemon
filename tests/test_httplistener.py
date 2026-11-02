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

from types import SimpleNamespace

import pytest
from pdudaemon.httplistener import HTTPListener
from pdudaemon.pdurunner import PDURunner


@pytest.fixture
def http_listener(mocker):
    mocker.patch("pdudaemon.pdurunner.time.sleep")
    config = {"daemon": {"hostname": "localhost"},
              "pdus": {"dummy": {"driver": "localcmdline"}}}
    runner = PDURunner(config["pdus"]["dummy"], "dummy", 5, 0)
    yield HTTPListener(config, SimpleNamespace(runners={"dummy": runner}))
    runner.executor.shutdown()


def make_request(command):
    return SimpleNamespace(remote="127.0.0.1",
                           path_qs="/power/control/%s?hostname=dummy&port=1" % command)


@pytest.mark.asyncio
async def test_failed_request_returns_500(mocker, http_listener):
    runner = http_listener.daemon.runners["dummy"]
    mocker.patch.object(runner.driver, "port_on", side_effect=OSError("nope"))

    resp = await http_listener.handle(make_request("on"))

    assert resp.status == 500
    assert resp.text.startswith("Request failed: ")
