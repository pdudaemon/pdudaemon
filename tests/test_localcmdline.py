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
