#!/usr/bin/python3

#  Copyright 2013 Linaro Limited
#  Author Matt Hart <matthew.hart@linaro.org>
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
import socket
import pdudaemon.listener as listener
logger = logging.getLogger('pdud.tcp')


class TCPListener:

    def __init__(self, config, daemon):
        self.config = config
        self.daemon = daemon
        self.settings = config["daemon"]

        self.server = None

    async def start(self):
        listen_host = self.settings["hostname"]
        listen_port = self.settings.get("port", 16421)
        logger.info("listening on %s:%s", listen_host, listen_port)
        self.server = await asyncio.start_server(
            client_connected_cb=self.handle,
            host=listen_host,
            port=listen_port,
            reuse_address=True,
        )

    async def shutdown(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.server = None

    async def insert_request(self, data):
        args = listener.parse_tcp(data)
        if args:
            return await listener.process_request(args, self.config, self.daemon)

    async def handle(self, reader, writer):
        request_ip = writer.get_extra_info('peername')[0]
        loop = asyncio.get_running_loop()
        try:
            data = await reader.read(16384)
            data = data.decode('utf-8')
            data = data.strip()
            try:
                fut = loop.run_in_executor(None, socket.gethostbyaddr, request_ip)
                request_host = (await asyncio.wait_for(fut, timeout=2))[0]
            except (socket.herror, asyncio.TimeoutError):
                request_host = request_ip
            logger.info("Received a request from %s: '%s'", request_host, data)
            res = await self.insert_request(data)
            if res:
                writer.write("ack\n".encode('utf-8'))
            else:
                writer.write("nack\n".encode('utf-8'))
        except Exception as global_error:  # pylint: disable=broad-except
            logger.debug(global_error.__class__)
            logger.debug(global_error)
            writer.write(str(global_error).encode('utf-8'))
        writer.close()
        await writer.wait_closed()
