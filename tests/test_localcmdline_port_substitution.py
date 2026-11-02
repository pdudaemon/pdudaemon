#!/usr/bin/python3
"""Tests for port number substitution in the localcmdline driver."""

from unittest.mock import ANY

import pytest
from pdudaemon.drivers.localcmdline import LocalCmdline


@pytest.mark.parametrize(
    "command, port_number, expected",
    [
        ("echo %s", 3, "echo 3"),
        ("echo %s", "3", "echo 3"),
        ("echo %s", "test", "echo test"),
        ("echo %d", 3, "echo 3"),
        ("echo %i", 3, "echo 3"),
        ("echo %03d", 3, "echo 003"),
        ("relay --pct 50%% --port %i", 3, "relay --pct 50% --port 3"),
    ],
)
@pytest.mark.parametrize("request_name", ["on", "off"])
def test_port_substitution(mocker, request_name, command, port_number, expected):
    run_command = mocker.patch("pdudaemon.drivers.localcmdline.run_command")
    pdu = LocalCmdline("dummy", {"cmd_" + request_name: command})

    pdu.port_interaction(request_name, port_number)

    run_command.assert_called_once_with(ANY, expected, shell=True)
