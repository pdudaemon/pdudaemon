from unittest.mock import AsyncMock, MagicMock, call

import pytest
from pdudaemon import listener


@pytest.fixture
def config():
    return {
        "pdus": {"pdu1": {}, "pdu2": {}},
        "aliases": {"board1": {"hostname": "pdu1", "port": 1}},
        "groups": {
            "rack": ["board1", {"hostname": "pdu2", "port": 2}],
            "badalias": ["board1", "missing"],
            "badpdu": ["board1", {"hostname": "missing", "port": 2}],
            "noport": ["board1", {"hostname": "pdu2"}],
        },
    }


@pytest.fixture
def daemon():
    daemon = MagicMock()
    daemon.runners = {
        "pdu1": MagicMock(do_job_async=AsyncMock(return_value=True)),
        "pdu2": MagicMock(do_job_async=AsyncMock(return_value=True)),
    }
    return daemon


def group_args(group, request="on", **kwargs):
    args = listener.Args()
    args.group = group
    args.request = request
    for key, value in kwargs.items():
        setattr(args, key, value)
    return args


def test_parse_http_group():
    args = listener.parse_http({"group": ["rack"]}, "/power/control/on")

    assert args.group == "rack"
    assert args.request == "on"


@pytest.mark.asyncio
async def test_group_runs_every_member(config, daemon):
    assert await listener.process_request(group_args("rack"), config, daemon)

    daemon.runners["pdu1"].do_job_async.assert_awaited_once_with(1, "on")
    daemon.runners["pdu2"].do_job_async.assert_awaited_once_with(2, "on")


@pytest.mark.asyncio
async def test_group_reboot(config, daemon):
    args = group_args("rack", request="reboot", delay="0")

    assert await listener.process_request(args, config, daemon)

    assert daemon.runners["pdu1"].do_job_async.await_args_list == [call(1, "off"), call(1, "on")]
    assert daemon.runners["pdu2"].do_job_async.await_args_list == [call(2, "off"), call(2, "on")]


@pytest.mark.asyncio
async def test_group_fails_if_any_member_fails(config, daemon):
    daemon.runners["pdu1"].do_job_async.return_value = False

    assert not await listener.process_request(group_args("rack"), config, daemon)

    daemon.runners["pdu2"].do_job_async.assert_awaited_once_with(2, "on")


@pytest.mark.asyncio
@pytest.mark.parametrize("group", ["unknown", "badalias", "badpdu", "noport"])
async def test_invalid_group_runs_nothing(config, daemon, group):
    assert not await listener.process_request(group_args(group), config, daemon)

    daemon.runners["pdu1"].do_job_async.assert_not_awaited()
    daemon.runners["pdu2"].do_job_async.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [{"alias": "board1"}, {"hostname": "pdu1"}, {"port": "1"}])
async def test_group_cannot_be_combined(config, daemon, extra):
    assert not await listener.process_request(group_args("rack", **extra), config, daemon)

    daemon.runners["pdu1"].do_job_async.assert_not_awaited()
    daemon.runners["pdu2"].do_job_async.assert_not_awaited()
