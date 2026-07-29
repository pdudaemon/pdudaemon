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
import time
import traceback
import pexpect
import concurrent.futures
from pdudaemon.drivers.driver import FailedRequestException, PDUDriver
import pdudaemon.drivers.strategies

assert pdudaemon.drivers.strategies, "Subclasses are iterated to find all drivers"

class PDURunner:

    def __init__(self, config, hostname, retries, retrydelay):
        self.config = config
        self.hostname = hostname
        self.retries = retries
        self.retrydelay = retrydelay
        self.logger = logging.getLogger("pdud.pdu.%s" % hostname)
        self.driver = self.driver_from_hostname(hostname)
        # use single-worker ThreadPoolExecutor to serialize execution
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix=hostname)

    async def shutdown(self):
        self.executor.shutdown(wait=True, cancel_futures=True)

    def driver_from_hostname(self, hostname):
        drivername = self.config['driver']
        driver = PDUDriver.select(drivername)(hostname, self.config)
        return driver

    def _run_with_retries(self, port, request, action):
        self.logger.info("Processing job for PDU %s: (%s %s)", self.hostname, request, port)
        retries = self.retries
        while retries > 0:
            try:
                result = action()
                self.driver._cleanup()  # pylint: disable=W0212
                return result
            except (OSError, pexpect.exceptions.EOF, Exception):  # pylint: disable=broad-except
                self.logger.warn(traceback.format_exc())
                self.logger.warn("Failed to execute job: {} {} (attempts left {})".format(port, request, retries - 1))
                if self.driver:
                    self.driver._bombout()  # pylint: disable=W0212,E1101
                time.sleep(self.retrydelay)
                retries -= 1
                continue
        raise FailedRequestException(
            "Failed to {} port {} on PDU {} after {} retries".format(request, port, self.hostname, self.retries)
        )

    def port_on(self, port):
        self._run_with_retries(port, "on", lambda: self.driver.port_on(port))

    def port_off(self, port):
        self._run_with_retries(port, "off", lambda: self.driver.port_off(port))

    def get_port_state(self, port) -> bool:
        return self._run_with_retries(port, "get-port-state", lambda: self.driver.get_port_state(port))

    async def _in_executor(self, fn, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, fn, *args)

    async def port_on_async(self, port) -> None:
        await self._in_executor(self.port_on, port)

    async def port_off_async(self, port) -> None:
        await self._in_executor(self.port_off, port)

    async def get_port_state_async(self, port) -> bool:
        return await self._in_executor(self.get_port_state, port)
