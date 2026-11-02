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
from types import SimpleNamespace

import pytest

from pdudaemon import MultiLineFormatter, setup_logging


def make_record(msg, exc_info=None):
    return logging.LogRecord("pdud", logging.WARNING, __file__, 1, msg, None, exc_info)


def test_single_line():
    formatter = MultiLineFormatter("%(levelname)s %(message)s")

    assert formatter.format(make_record("one")) == "WARNING one"


def test_multi_line():
    formatter = MultiLineFormatter("%(levelname)s %(message)s")

    assert formatter.format(make_record("one\ntwo")) == "WARNING one\nWARNING two"


def test_exception():
    formatter = MultiLineFormatter("%(levelname)s %(message)s")
    try:
        raise ValueError("oops")
    except ValueError as exc:
        exc_info = (type(exc), exc, exc.__traceback__)

    lines = formatter.format(make_record("failed", exc_info)).split("\n")

    assert lines[0] == "WARNING failed"
    assert lines[1] == "WARNING Traceback (most recent call last):"
    assert lines[-1] == "WARNING ValueError: oops"


@pytest.fixture
def restore_logging():
    root = logging.getLogger()
    pdud = logging.getLogger("pdud")
    handlers, root_level, pdud_level = root.handlers[:], root.level, pdud.level
    yield
    root.handlers[:] = handlers
    root.setLevel(root_level)
    pdud.setLevel(pdud_level)
    logging.getLogger("aiohttp.access").setLevel(logging.NOTSET)


@pytest.mark.parametrize("loglevel, library_level", [
    ("WARNING", logging.WARNING),
    ("INFO", logging.INFO),
    ("DEBUG", logging.INFO),
    ("TRACE", logging.DEBUG),
])
def test_library_level(restore_logging, loglevel, library_level):
    options = SimpleNamespace(journal=False, logfile="-", logformat=None,
                              loglevel=loglevel, drive=False)

    setup_logging(options, {})

    assert logging.getLogger("paramiko").getEffectiveLevel() == library_level


@pytest.mark.parametrize("loglevel,access_level", [
    ("INFO", logging.WARNING),
    ("DEBUG", logging.WARNING),
    ("TRACE", logging.DEBUG),
])
def test_access_log_level(restore_logging, loglevel, access_level):
    options = SimpleNamespace(journal=False, logfile="-", logformat=None,
                              loglevel=loglevel, drive=False)

    setup_logging(options, {})

    assert logging.getLogger("aiohttp.access").getEffectiveLevel() == access_level
