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
from subprocess import CalledProcessError
from pdudaemon.drivers.driver import UnknownCommandException
from pdudaemon.drivers.localcmdline import LocalCmdline


@pytest.mark.parametrize(
    "command, port_number, expected",
    [
        ("echo %s", 3, "echo 3"),
        ("echo %s", "3", "echo 3"),
        ("echo %s", "test", "echo test"),
        ("echo %d", 3, "echo 3"),
        ("echo on", 3, "echo on"),
        ("echo on", "3", "echo on"),
        ("echo on", "test", "echo on"),
        ("echo 50%%", 3, "echo 50%"),
        ("echo %(port)s", 3, "echo 3"),
        ("echo %(port)02d", 3, "echo 03"),
        ("echo %(hostname)s %(port)s", 3, "echo dummy 3"),
        ("echo %(serial)s %(port)s", 3, "echo 262305 3"),
        ("echo %(serial)s 50%%", 3, "echo 262305 50%"),
    ],
)
def test_port_interaction(mocker, command, port_number, expected):
    call = mocker.patch("pdudaemon.drivers.localcmdline.call")
    pdu = LocalCmdline("dummy", {"cmd_on": command, "serial": "262305"})

    pdu.port_interaction("on", port_number)

    call.assert_called_once_with(expected, shell=True)


def test_port_interaction_unknown_command(mocker):
    call = mocker.patch("pdudaemon.drivers.localcmdline.call")
    pdu = LocalCmdline("dummy", {"cmd_on": "echo on"})

    pdu.port_interaction("reboot", 1)

    call.assert_not_called()


def test_port_interaction_missing_setting(mocker):
    call = mocker.patch("pdudaemon.drivers.localcmdline.call")
    pdu = LocalCmdline("dummy", {"cmd_on": "echo %(serial)s"})

    with pytest.raises(KeyError):
        pdu.port_interaction("on", 1)

    call.assert_not_called()


@pytest.mark.parametrize(
    "output, expected",
    [
        ("on\n", True),
        ("on", True),
        ("off\n", False),
        (" off ", False),
    ],
)
def test_get_port_state(mocker, output, expected):
    check_output = mocker.patch("pdudaemon.drivers.localcmdline.check_output",
                                return_value=output)
    pdu = LocalCmdline("dummy", {"cmd_state": "cat /tmp/%(hostname)s-%(port)s"})

    assert pdu.get_port_state(3) is expected

    check_output.assert_called_once_with("cat /tmp/dummy-3", shell=True, text=True)


@pytest.mark.parametrize("output", ["maybe\n", "1\n", "0\n", "ON\n", ""])
def test_get_port_state_unexpected_output(mocker, output):
    mocker.patch("pdudaemon.drivers.localcmdline.check_output", return_value=output)
    pdu = LocalCmdline("dummy", {"cmd_state": "echo maybe"})

    with pytest.raises(RuntimeError):
        pdu.get_port_state(1)


def test_get_port_state_unsupported(mocker):
    check_output = mocker.patch("pdudaemon.drivers.localcmdline.check_output")
    pdu = LocalCmdline("dummy", {"cmd_on": "echo on"})

    with pytest.raises(UnknownCommandException):
        pdu.get_port_state(1)

    check_output.assert_not_called()


def test_get_port_state_command(tmp_path):
    state = tmp_path / "state"
    state.write_text("on\n")
    pdu = LocalCmdline("dummy", {"cmd_state": "cat %s" % state})

    assert pdu.get_port_state(1) is True


def test_get_port_state_command_fails():
    pdu = LocalCmdline("dummy", {"cmd_state": "echo on; exit 1"})

    with pytest.raises(CalledProcessError):
        pdu.get_port_state(1)
