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

import logging

import pytest

from pdudaemon.drivers.driver import FailedRequestException, run_command

log = logging.getLogger("test")


def test_output(caplog):
    caplog.set_level(logging.DEBUG)

    run_command(log, ["sh", "-c", "echo one; echo two"])

    assert caplog.messages == ["Running command: sh -c 'echo one; echo two'",
                               "Output of command sh -c 'echo one; echo two':\n"
                               "| one\n| two"]


def test_no_output(caplog):
    caplog.set_level(logging.DEBUG)

    run_command(log, ["true"])

    assert caplog.messages == ["Running command: true"]


def test_check_failed():
    with pytest.raises(FailedRequestException,
                       match="^sh -c 'exit 3' exited with status 3$"):
        run_command(log, ["sh", "-c", "exit 3"])


def test_no_check_failed():
    assert run_command(log, ["sh", "-c", "exit 3"], check=False).returncode == 3
