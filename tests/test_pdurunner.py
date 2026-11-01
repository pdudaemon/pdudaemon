#!/usr/bin/python3
"""Tests for PDURunner."""

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


def test_failed_request_keeps_cached_state(mocker, runner):
    mocker.patch.object(runner.driver, "port_on")
    runner.port_on(1)
    mocker.patch.object(runner.driver, "port_off", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        runner.port_off(1)

    assert runner.get_cached_port_state(1) is True


def test_get_cached_port_state_does_not_query_driver(mocker, runner):
    port_interaction = mocker.patch.object(runner.driver, "port_interaction")

    runner.get_cached_port_state(1)

    port_interaction.assert_not_called()


def test_set_cached_port_state(runner):
    runner._set_cached_port_state(1, True)
    assert runner.get_cached_port_state("1") is True

    runner._set_cached_port_state("1", False)
    assert runner.get_cached_port_state(1) is False
