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


@pytest.mark.parametrize("on", [True, False])
def test_get_port_state_updates_cache(mocker, runner, on):
    mocker.patch.object(runner.driver, "get_port_state", return_value=on)

    assert runner.get_port_state(1) is on
    assert runner.get_cached_port_state(1) is on


def test_failed_request_keeps_cached_state(mocker, runner):
    mocker.patch.object(runner.driver, "port_on")
    runner.port_on(1)
    mocker.patch.object(runner.driver, "port_off", side_effect=OSError("nope"))

    with pytest.raises(FailedRequestException):
        runner.port_off(1)

    assert runner.get_cached_port_state(1) is True


def test_get_cached_port_state_does_not_query_driver(mocker, runner):
    get_port_state = mocker.patch.object(runner.driver, "get_port_state")

    runner.get_cached_port_state(1)

    get_port_state.assert_not_called()


def test_set_cached_port_state(runner):
    runner._set_cached_port_state(1, True)
    assert runner.get_cached_port_state("1") is True

    runner._set_cached_port_state("1", False)
    assert runner.get_cached_port_state(1) is False


def test_get_cached_port_states(runner):
    assert runner.get_cached_port_states() == {}

    runner._set_cached_port_state(1, True)
    runner._set_cached_port_state("2", False)
    states = runner.get_cached_port_states()
    assert states == {"1": True, "2": False}

    # the returned dict is a copy, so callers can't change the cache
    states["1"] = False
    assert runner.get_cached_port_state(1) is True


def test_get_ports_unknown(runner):
    assert runner.driver.get_ports() == []


def test_get_ports_port_count():
    runner = PDURunner({"driver": "localcmdline", "port_count": "3"}, "dummy", 1, 0)

    assert runner.driver.port_count == 3
    assert runner.driver.get_ports() == [1, 2, 3]


@pytest.mark.parametrize("first_port, ports", [(0, [0, 1, 2]), ("1", [1, 2, 3])])
def test_get_ports_first_port(first_port, ports):
    runner = PDURunner({"driver": "localcmdline", "port_count": 3, "first_port": first_port}, "dummy", 1, 0)

    assert runner.driver.get_ports() == ports


@pytest.mark.parametrize("first_port", [-1, 2])
def test_first_port_invalid(first_port):
    with pytest.raises(ValueError):
        PDURunner({"driver": "localcmdline", "port_count": 3, "first_port": first_port}, "dummy", 1, 0)


def test_port_count_does_not_override_driver():
    runner = PDURunner({"driver": "devantech_USB-RLY04", "port_count": 8}, "dummy", 1, 0)

    assert runner.driver.port_count == 4
    assert runner.driver.get_ports() == [1, 2, 3, 4]


def test_first_port_with_driver_port_count():
    runner = PDURunner({"driver": "devantech_USB-RLY04", "first_port": 0}, "dummy", 1, 0)

    assert runner.driver.get_ports() == [0, 1, 2, 3]


def test_first_port_overrides_driver():
    runner = PDURunner({"driver": "intellinet", "first_port": 1}, "dummy", 1, 0)

    assert runner.driver.first_port == 1


@pytest.mark.parametrize("port_count", [None, 2, 8])
def test_get_ports_port_names(port_count):
    config = {"driver": "localcmdline", "port_names": ["switch.board", 2]}
    if port_count is not None:
        config["port_count"] = port_count
    runner = PDURunner(config, "dummy", 1, 0)

    assert runner.driver.get_ports() == ["switch.board", "2"]
