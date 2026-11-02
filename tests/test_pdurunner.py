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

import asyncio
import pytest
from pdudaemon.pdurunner import PDURunner
from pdudaemon.drivers.driver import FailedRequestException, UnknownCommandException


@pytest.fixture
def runner(mocker):
    mocker.patch("pdudaemon.pdurunner.time.sleep")
    return PDURunner({"driver": "localcmdline"}, "dummy", 5, 0)


@pytest.mark.parametrize("request_", ["port_on", "port_off"])
def test_request_calls_driver(mocker, runner, request_):
    driver_request = mocker.patch.object(runner.driver, request_)
    cleanup = mocker.patch.object(runner.driver, "_cleanup")
    bombout = mocker.patch.object(runner.driver, "_bombout")

    getattr(runner, request_)(1)

    driver_request.assert_called_once_with(1)
    cleanup.assert_called_once_with()
    bombout.assert_not_called()


def test_unknown_command_is_not_retried(mocker, runner):
    port_on = mocker.patch.object(runner.driver, "port_on",
                                  side_effect=UnknownCommandException("nope"))
    bombout = mocker.patch.object(runner.driver, "_bombout")

    with pytest.raises(UnknownCommandException):
        runner.port_on(1)

    port_on.assert_called_once_with(1)
    bombout.assert_not_called()


def test_unsupported_get_port_state_is_not_retried(mocker, runner):
    get_port_state = mocker.spy(runner.driver, "get_port_state")

    with pytest.raises(UnknownCommandException):
        runner.get_port_state(1)

    get_port_state.assert_called_once_with(1)


def test_failure_is_retried(mocker, runner):
    port_on = mocker.patch.object(runner.driver, "port_on", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        runner.port_on(1)

    assert port_on.call_count == 5


@pytest.mark.parametrize("request_", ["port_on", "port_off", "get_port_state"])
def test_failure_bombs_out_and_waits(mocker, runner, request_):
    sleep = mocker.patch("pdudaemon.pdurunner.time.sleep")
    mocker.patch.object(runner.driver, request_, side_effect=OSError("nope"))
    bombout = mocker.patch.object(runner.driver, "_bombout")
    cleanup = mocker.patch.object(runner.driver, "_cleanup")
    runner.retrydelay = 3

    with pytest.raises(FailedRequestException):
        getattr(runner, request_)(1)

    assert bombout.call_count == 5
    assert sleep.call_count == 5
    sleep.assert_called_with(3)
    cleanup.assert_not_called()


@pytest.mark.parametrize("request_, expected", [
    ("port_on", True),
    ("port_off", False),
])
def test_transient_failure_recovers(mocker, runner, request_, expected):
    driver_request = mocker.patch.object(runner.driver, request_,
                                         side_effect=[OSError("nope"), None])

    getattr(runner, request_)(1)

    assert driver_request.call_count == 2
    assert runner.get_cached_port_state(1) is expected


def test_get_port_state_transient_failure_recovers(mocker, runner):
    get_port_state = mocker.patch.object(runner.driver, "get_port_state",
                                         side_effect=[OSError("nope"), True])

    assert runner.get_port_state(1) is True

    assert get_port_state.call_count == 2


def test_get_port_state_returns_driver_result(mocker, runner):
    mocker.patch.object(runner.driver, "get_port_state", return_value=True)

    assert runner.get_port_state(1) is True


def test_port_state_unknown(runner):
    assert runner.get_cached_port_state(1) is None


@pytest.mark.parametrize("request_, expected", [
    ("port_on", True),
    ("port_off", False),
])
def test_port_state_cached(mocker, runner, request_, expected):
    mocker.patch.object(runner.driver, request_)

    getattr(runner, request_)(1)

    assert runner.get_cached_port_state(1) is expected
    assert runner.get_cached_port_state("1") is expected
    assert runner.get_cached_port_state(2) is None


def test_failed_request_clears_cached_state(mocker, runner):
    mocker.patch.object(runner.driver, "port_on")
    runner.port_on(1)
    mocker.patch.object(runner.driver, "port_off", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        runner.port_off(1)

    assert runner.get_cached_port_state(1) is None


def test_failed_get_port_state_keeps_cached_state(mocker, runner):
    mocker.patch.object(runner.driver, "port_on")
    runner.port_on(1)
    mocker.patch.object(runner.driver, "get_port_state", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        runner.get_port_state(1)

    assert runner.get_cached_port_state(1) is True


def test_unknown_command_clears_cached_state(mocker, runner):
    mocker.patch.object(runner.driver, "port_on")
    runner.port_on(1)
    mocker.patch.object(runner.driver, "port_off",
                        side_effect=UnknownCommandException("nope"))

    with pytest.raises(UnknownCommandException):
        runner.port_off(1)

    assert runner.get_cached_port_state(1) is None


def test_get_cached_port_state_does_not_query_driver(mocker, runner):
    get_port_state = mocker.patch.object(runner.driver, "get_port_state")

    runner.get_cached_port_state(1)

    get_port_state.assert_not_called()


@pytest.mark.parametrize("on", [True, False])
def test_get_port_state_updates_cache(mocker, runner, on):
    mocker.patch.object(runner.driver, "get_port_state", return_value=on)

    assert runner.get_port_state(1) is on
    assert runner.get_cached_port_state(1) is on


@pytest.mark.parametrize("request_, expected", [
    ("port_on", True),
    ("port_off", False),
])
def test_request_async(mocker, runner, request_, expected):
    driver_request = mocker.patch.object(runner.driver, request_)

    assert asyncio.run(getattr(runner, request_ + "_async")(1)) is None

    driver_request.assert_called_once_with(1)
    assert runner.get_cached_port_state(1) is expected


def test_get_port_state_async(mocker, runner):
    mocker.patch.object(runner.driver, "get_port_state", return_value=True)

    assert asyncio.run(runner.get_port_state_async(1)) is True
    assert runner.get_cached_port_state(1) is True


def test_failure_async(mocker, runner):
    mocker.patch.object(runner.driver, "port_on", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        asyncio.run(runner.port_on_async(1))
