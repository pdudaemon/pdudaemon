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
logger = logging.getLogger('pdud.listener')


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


async def process_request(args, config, daemon):
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
            logging.error("Trying to use and alias and also a hostname/port")
            return False
        # Using alias support, get all pdu info from alias
        alias_settings = (config.get('aliases', {})).get(args.alias, False)
        if not alias_settings:
            logging.error("Alias requested but not found")
            return False
        args.hostname = config["aliases"][args.alias]["hostname"]
        args.port = config["aliases"][args.alias]["port"]
    if not args.hostname or not args.port or not args.request:
        logger.info("One of hostname,port,request was not set")
        return False
    if args.hostname not in config['pdus']:
        logger.info("PDU was not found in config")
        return False
    if args.request not in ["reboot", "on", "off"]:
        logger.info("Unknown request: %s", args.request)
        return False
    runner = daemon.runners[args.hostname]
    if args.request == "reboot":
        logger.debug("reboot requested, submitting off/on")
        await runner.do_job_async(args.port, "off")
        await asyncio.sleep(int(args.delay))
        await runner.do_job_async(args.port, "on")
        return True
    else:
        await asyncio.sleep(int(args.delay))
        await runner.do_job_async(args.port, args.request)
        return True
