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
import collections
import contextlib
import enum
import json
import logging

import aiohttp.web


# for example nginx's "proxy_read_timeout" defaults to 60 seconds
POLLING_KEEPALIVE_PERIOD_SECONDS = 50


logger = logging.getLogger('pdud.listener')


class PortEvent(collections.namedtuple("PortEvent", ("port", "state"))):

    def serialize(self):
        return {
            "port": str(self.port),
            "is_powered": self.state == PortState.ON,
        }


class PortState(enum.Enum):
    ON = "on"
    OFF = "off"


class EventCollector:

    def __init__(self):
        self._listener_queues = []

    @contextlib.contextmanager
    def get_listener(self) -> asyncio.Queue:
        listener_queue = asyncio.Queue()
        self._listener_queues.append(listener_queue)
        try:
            yield listener_queue
        finally:
            self._listener_queues.remove(listener_queue)

    async def notify(self, port_event: PortEvent) -> None:
        for queue in list(self._listener_queues):
            await queue.put(port_event)

    async def cleanup(self):
        # listeners are supposed to treat a None as a signal for stopping
        await self.notify(None)


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


async def process_request(args, config, daemon, request, event_collector: EventCollector):
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
    if args.request == "subscribe":
        response = aiohttp.web.StreamResponse()
        await response.prepare(request)
        with event_collector.get_listener() as listener:
            while True:
                try:
                    event = await asyncio.wait_for(
                        listener.get(), timeout=POLLING_KEEPALIVE_PERIOD_SECONDS
                    )
                except asyncio.TimeoutError:
                    # We should send a bit of data from time to time in order to prevent
                    # proxy servers from killing our connection.
                    data = {}
                else:
                    if event is None:
                        # the collector signals, that we should stop listening
                        break
                    data = event.serialize()
                await response.write(json.dumps(data).encode() + b'\n')
        await response.write_eof()
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
        await event_collector.notify(PortEvent(int(args.port), PortState.OFF))
        await runner.do_job_async(int(args.port), "off")
        await asyncio.sleep(int(args.delay))
        await event_collector.notify(PortEvent(int(args.port), PortState.ON))
        await runner.do_job_async(int(args.port), "on")
        return True
    else:
        await asyncio.sleep(int(args.delay))
        await event_collector.notify(PortEvent(int(args.port), PortState.ON if args.request == "on" else PortState.OFF))
        await runner.do_job_async(int(args.port), args.request)
        return True
