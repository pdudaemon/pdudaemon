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
from importlib.resources import files

logger = logging.getLogger('pdud.http')

STATUS_HTML = files("pdudaemon").joinpath("static/status.html").read_text()


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
            web.get('/power/control/get-cached-port-state', self.handle),
            web.get('/power/control/get-port-state', self.handle),
            web.get('/power/status', self.handle_status),
            web.get('/power/status/json', self.handle_status),
        ])
        if self.settings.get("web_ui", False):
            self.app.add_routes([
                web.get('/', self.handle_index),
                web.get('/power/dashboard', self.handle_dashboard),
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
        if isinstance(res, listener.PortStatus):
            return web.Response(status=200, content_type="application/json",
                                text='{"state": "%s"}\n' % res.state)
        if isinstance(res, listener.CommandAccepted):
            return web.Response(status=200, text="OK - accepted request\n")
        if isinstance(res, listener.RequestError):
            return web.Response(status=500, text="Invalid request: %s\n" % res.message)
        return web.Response(status=500, text="Invalid request\n")

    async def insert_request(self, data, path):
        args = listener.parse_http(data, path)
        if not args:
            return listener.RequestError("could not parse request")
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
        alias_names = self.get_alias_names()
        for name, runner in runners.items():
            aliases = alias_names.get(name, {})
            ports = {str(port): {"state": "unknown"} for port in runner.driver.get_ports()}
            for port in aliases:
                ports[port] = {"state": "unknown"}
            for port, on in runner.get_cached_port_states().items():
                ports[port] = {"state": listener.PortStatus(on=on).state}
            for port, alias in aliases.items():
                ports[port]["alias"] = alias
            status[name] = {
                "driver": runner.config["driver"],
                "get_port_state": runner.driver.supports_get_port_state(),
                "ports": ports,
            }
            warning = runner.get_ports_warning()
            if warning:
                status[name]["warning"] = warning
        if hostname:
            return {hostname: status[hostname]}
        return status

    async def handle_status(self, request):
        status = self.get_status(request)
        if status is None:
            return web.Response(status=404, text="PDU not found\n")
        return web.json_response(status)

    async def handle_index(self, request):
        raise web.HTTPFound('/power/dashboard')

    async def handle_dashboard(self, request):
        if self.get_status(request) is None:
            return web.Response(status=404, text="PDU not found\n")
        return web.Response(content_type="text/html", text=STATUS_HTML)
