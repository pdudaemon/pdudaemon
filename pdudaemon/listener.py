#!/usr/bin/python3

#  Copyright 2019 Matt Hart <matt@mattface.org>
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

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger('pdud.listener')


class RequestResult:
    """Base class for typed results returned by process_request."""
    pass


@dataclass
class CommandAccepted(RequestResult):
    """A set-style command (on/off/reboot) was successfully accepted."""
    pass


@dataclass
class PortStatus(RequestResult):
    """Result of a get-port-state request - True if the port is powered on."""
    on: bool


@dataclass
class RequestError(RequestResult):
    """The request was rejected or failed."""
    message: str


class Args(object):
    hostname = None
    alias = None
    request = None
    port = None
    pass


def parse_tcp(data):
    args = Args()
    delay = None
    array = data.split(" ")
    if (len(array) < 3) or (len(array) > 4):
        logger.info("Wrong data size")
        raise Exception("Unexpected data")
    if len(array) == 4:
        delay = int(array[3])
    args.hostname = array[0]
    args.port = int(array[1])
    args.request = array[2]
    args.delay = delay
    return args


def parse_http(data, path):
    args = Args()
    entry = path.lstrip('/').split('/')
    if len(entry) != 3:
        logger.info("Request path was invalid: %s", entry)
        return False
    if not (entry[0] == 'power' and entry[1] == 'control'):
        logger.info("Unknown request, path was %s", path)
        return False
    # everything comes back from the http library in a 1 sized list
    args.alias = data.get('alias', [None])[0]
    args.hostname = data.get('hostname', [None])[0]
    args.port = data.get('port', [None])[0]
    args.request = entry[2]
    args.delay = data.get('delay', [None])[0]
    return args


def _resolve_args(args, config):
    """Validate args and resolve any alias. Returns a RequestError on failure,
    or None on success (mutating args in place).
    """
    if args.request in ["on", "off"] and args.delay is not None:
        logger.warn("delay parameter is deprecated for on/off commands")
    if args.delay is not None:
        logger.debug("using custom delay as requested")
    else:
        # this has been a default since the start, it should be smaller but I
        # can't really change expected behaviour now
        if args.request == "reboot":
            args.delay = 5
        else:
            args.delay = 0
    if args.alias:
        if args.hostname or args.port:
            logger.error("Trying to use and alias and also a hostname/port")
            return RequestError("alias cannot be combined with hostname/port")
        alias_settings = (config.get('aliases', {})).get(args.alias, False)
        if not alias_settings:
            logger.error("Alias requested but not found")
            return RequestError("alias not found")
        args.hostname = config["aliases"][args.alias]["hostname"]
        args.port = config["aliases"][args.alias]["port"]
    if not args.hostname or not args.port or not args.request:
        logger.info("One of hostname,port,request was not set")
        return RequestError("hostname, port or request was not set")
    if args.hostname not in config['pdus']:
        logger.info("PDU was not found in config")
        return RequestError("PDU not found in config")
    if args.request not in ["reboot", "on", "off", "get-port-state"]:
        logger.info("Unknown request: %s", args.request)
        return RequestError("unknown request: %s" % args.request)
    return None


async def process_request(args, config, daemon) -> RequestResult:
    err = _resolve_args(args, config)
    if err is not None:
        return err
    runner = daemon.runners[args.hostname]
    try:
        if args.request == "reboot":
            logger.debug("reboot requested, submitting off/on")
            await runner.port_off_async(args.port)
            await asyncio.sleep(int(args.delay))
            await runner.port_on_async(args.port)
            return CommandAccepted()
        if args.request == "get-port-state":
            on = await runner.get_port_state_async(args.port)
            return PortStatus(on=on)
        await asyncio.sleep(int(args.delay))
        if args.request == "on":
            await runner.port_on_async(args.port)
        else:  # "off"
            await runner.port_off_async(args.port)
        return CommandAccepted()
    except Exception as exc:  # pylint: disable=broad-except
        logger.warn("Request failed: %s", exc)
        return RequestError(str(exc))
