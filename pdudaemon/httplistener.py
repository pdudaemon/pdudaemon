#!/usr/bin/python3

#  Copyright 2018 Matt Hart <matt@mattface.org>
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

import urllib.parse as urlparse
import logging
import pdudaemon.listener as listener

from aiohttp import web

logger = logging.getLogger('pdud.http')


class HTTPListener:

    def __init__(self, config, daemon):
        self.config = config
        self.daemon = daemon
        self.settings = config["daemon"]

        self.app = web.Application()
        self.app.add_routes([
            web.get('/power/control/on', self.handle),
            web.get('/power/control/off', self.handle),
            web.get('/power/control/reboot', self.handle),
        ])
        self.apprunner = None

    async def start(self):
        logger.info("Starting the HTTP server")
        self.apprunner = web.AppRunner(self.app)
        await self.apprunner.setup()
        listen_host = self.settings["hostname"]
        listen_port = self.settings.get("port", 16421)
        site = web.TCPSite(self.apprunner, host=listen_host, port=listen_port)
        await site.start()
        logger.info("Listening on %s:%s", listen_host, listen_port)

    async def shutdown(self):
        if self.apprunner:
            await self.apprunner.cleanup()
        self.apprunner = None

    async def handle(self, request):
        logger.info("Handling HTTP request from %s: %s", request.remote, request.path_qs)
        data = urlparse.parse_qs(urlparse.urlparse(request.path_qs).query)
        path = urlparse.urlparse(request.path_qs).path
        res = await self.insert_request(data, path)
        if res:
            return web.Response(status=200, text="OK - accepted request\n")
        else:
            return web.Response(status=500, text="Invalid request\n")

    async def insert_request(self, data, path):
        args = listener.parse_http(data, path)
        if args:
            return await listener.process_request(args, self.config, self.daemon)
