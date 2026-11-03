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

from pdudaemon.drivers.driver import FailedRequestException
from pdudaemon.pdurunner import PDURunner


class FailingDriver:
    def __init__(self, exc):
        self.exc = exc

    def handle(self, request, port):
        raise self.exc

    def _bombout(self):
        pass


def make_runner(exc):
    runner = PDURunner.__new__(PDURunner)
    runner.hostname = "test"
    runner.retries = 1
    runner.retrydelay = 0
    runner.logger = logging.getLogger("pdud.pdu.test")
    runner.driver = FailingDriver(exc)
    return runner


@pytest.mark.parametrize("exc", [FailedRequestException("refused\nmore"),
                                 ConnectionRefusedError("refused\nmore")])
def test_expected_failure(caplog, exc):
    caplog.set_level(logging.INFO)
    assert not make_runner(exc).do_job("1", "on")
    record = caplog.records[-1]
    assert record.getMessage().endswith(": %s: refused" % type(exc).__name__)
    assert not record.exc_info


def test_expected_failure_debug(caplog):
    caplog.set_level(logging.DEBUG)
    make_runner(FailedRequestException("refused")).do_job("1", "on")
    assert caplog.records[-1].exc_info


def test_unexpected_failure(caplog):
    caplog.set_level(logging.INFO)
    make_runner(KeyError("bug")).do_job("1", "on")
    assert caplog.records[-1].exc_info
