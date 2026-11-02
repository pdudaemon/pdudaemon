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

from pdudaemon import MultiLineFormatter


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
