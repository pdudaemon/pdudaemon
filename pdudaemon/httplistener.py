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
from jinja2 import Environment, PackageLoader

logger = logging.getLogger('pdud.http')

templates = Environment(loader=PackageLoader("pdudaemon", "templates"), autoescape=True)


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
            web.get('/power/status', self.handle_status),
            web.get('/power/status/json', self.handle_status),
            web.get('/power/status/html', self.handle_status_html),
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

    def get_alias_names(self):
        alias_names = {}
        for name, alias in self.config.get('aliases', {}).items():
            if alias.get('hostname') in self.daemon.runners:
                alias_names.setdefault(alias['hostname'], {})[str(alias.get('port'))] = name
        return alias_names

    def get_status(self, request):
        hostname = request.query.get('hostname')
        runners = self.daemon.runners
        if hostname and hostname not in runners:
            return None
        status = {}
        for name, ports in self.get_alias_names().items():
            status[name] = {port: "unknown" for port in ports}
        for name, runner in runners.items():
            if runner.port_status:
                status.setdefault(name, {}).update(runner.port_status)
        if hostname:
            return {hostname: status.get(hostname, {})}
        return status

    async def handle_status(self, request):
        status = self.get_status(request)
        if status is None:
            return web.Response(status=404, text="PDU not found\n")
        return web.json_response(status)

    async def handle_status_html(self, request):
        status = self.get_status(request)
        if status is None:
            return web.Response(status=404, text="PDU not found\n")
        template = templates.get_template("status-html.jinja2")
        text = template.render(status_data=status, alias_names=self.get_alias_names())
        return web.Response(content_type="text/html", text=text)
