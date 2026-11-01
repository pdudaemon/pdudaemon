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

import json

import pytest
from pdudaemon import check_alias_ports, load_config
from pdudaemon.pdurunner import PDURunner


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


@pytest.mark.parametrize("alias", ['{"hostname": "pdu2", "port": 1}', '{"port": 1}'])
def test_alias_unknown_hostname(alias):
    with pytest.raises(ValueError, match="Alias board: PDU .* is not in the config"):
        load_config('{"pdus": {"pdu1": {"driver": "a"}}, "aliases": {"board": %s}}' % alias)


@pytest.mark.parametrize("port", [1, "1", "switch.board"])
def test_alias_port_type(port):
    load_config('{"pdus": {"pdu1": {"driver": "a"}}, "aliases": {"board": {"hostname": "pdu1", "port": %s}}}'
                % json.dumps(port))


@pytest.mark.parametrize("port", [None, "", True, 1.5, [1]])
def test_alias_port_type_invalid(port):
    with pytest.raises(ValueError, match="Alias board: port must be a port number or name"):
        load_config('{"pdus": {"pdu1": {"driver": "a"}}, "aliases": {"board": {"hostname": "pdu1", "port": %s}}}'
                    % json.dumps(port))


def test_alias_port_missing():
    with pytest.raises(ValueError, match="Alias board: port must be a port number or name, not None"):
        load_config('{"pdus": {"pdu1": {"driver": "a"}}, "aliases": {"board": {"hostname": "pdu1"}}}')


@pytest.mark.parametrize("config, port, expected", [
    ({}, 9, "9"),
    ({}, "switch.board", "switch.board"),
    ({"port_count": 3}, 3, "3"),
    ({"port_count": 3}, "03", "3"),
    ({"port_names": ["board"]}, "board", "board"),
])
def test_alias_port(config, port, expected):
    runners = {"pdu1": PDURunner({"driver": "localcmdline", **config}, "pdu1", 1, 0)}
    aliases = {"board": {"hostname": "pdu1", "port": port}}

    check_alias_ports(aliases, runners)

    assert aliases["board"]["port"] == expected


@pytest.mark.parametrize("config, port", [
    ({"port_count": 3}, 4),
    ({"port_count": 3}, "x"),
    ({"port_names": ["board"]}, "other"),
])
def test_alias_port_invalid(config, port):
    runners = {"pdu1": PDURunner({"driver": "localcmdline", **config}, "pdu1", 1, 0)}

    with pytest.raises(ValueError, match="Alias board: Port .* of PDU pdu1"):
        check_alias_ports({"board": {"hostname": "pdu1", "port": port}}, runners)
