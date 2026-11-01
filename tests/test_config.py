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

"""Tests for loading and checking the configuration file."""

import pytest
from pdudaemon import load_config


def test_load_config():
    settings = load_config('{"pdus": {"pdu1": {"driver": "localcmdline"}}}')

    assert settings == {"pdus": {"pdu1": {"driver": "localcmdline"}}}


def test_duplicate_pdu_names():
    with pytest.raises(ValueError, match="Duplicate PDU names: pdu1"):
        load_config('{"pdus": {"pdu1": {"driver": "a"}, "pdu2": {"driver": "b"}, "pdu1": {"driver": "c"}}}')


def test_duplicate_alias_names():
    with pytest.raises(ValueError, match="Duplicate alias names: board"):
        load_config('{"pdus": {"pdu1": {"driver": "a"}},'
                    ' "aliases": {"board": {"hostname": "pdu1", "port": 1}, "board": {"hostname": "pdu1", "port": 2}}}')
