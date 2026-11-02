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
from pdudaemon.pdurunner import PDURunner
from pdudaemon.drivers.driver import FailedRequestException, UnknownCommandException


@pytest.fixture
def runner(mocker):
    mocker.patch("pdudaemon.pdurunner.time.sleep")
    return PDURunner({"driver": "localcmdline"}, "dummy", 5, 0)


def test_unknown_command_is_not_retried(mocker, runner):
    port_on = mocker.patch.object(runner.driver, "port_on",
                                  side_effect=UnknownCommandException("nope"))
    bombout = mocker.patch.object(runner.driver, "_bombout")

    with pytest.raises(UnknownCommandException):
        runner.port_on(1)

    port_on.assert_called_once_with(1)
    bombout.assert_not_called()


def test_failure_is_retried(mocker, runner):
    port_on = mocker.patch.object(runner.driver, "port_on", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        runner.port_on(1)

    assert port_on.call_count == 5
