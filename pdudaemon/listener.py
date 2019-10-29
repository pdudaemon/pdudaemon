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

import logging
import time
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
    now = int(time.time())
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
    delay = None
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


def process_request(args, config, db_queue):
    if args.delay:
        logger.debug("using custom delay as requested")
    else:
        # this has been a default since the start, it should be smaller but I
        # can't really change expected behaviour now
        args.delay = 5
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
    if not (args.request in ["reboot", "on", "off"]):
        logger.info("Unknown request: %s", args.request)
        return False
    now = time.time()
    if args.request == "reboot":
        logger.debug("reboot requested, submitting off/on")
        db_queue.put(("CREATE", args.hostname, args.port, "off", now))
        db_queue.put(("CREATE", args.hostname, args.port, "on", now + int(args.delay)))
        return True
    else:
        db_queue.put(("CREATE", args.hostname, args.port, args.request, now + int(args.delay)))
        return True
