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
import threading
import time
import traceback
import pexpect
import concurrent.futures
from typing import Optional
from pdudaemon.drivers.driver import FailedRequestException, PDUDriver, UnknownCommandException
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
        # last known state of each port on this PDU, keyed by str(port);
        # only access through get_cached_port_state(), get_cached_port_states()
        # and _set_cached_port_state()
        self.port_state_cache = {}
        # time.time() the cached state of each port last changed, keyed by
        # str(port)
        self.port_state_changed = {}
        # use single-worker ThreadPoolExecutor to serialize execution
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix=hostname)
        # set on shutdown to stop retrying the running job
        self.stopping = threading.Event()
        # True while the driver is running a job
        self.busy = False

    async def shutdown(self):
        """Cancel the queued jobs and stop retrying the running job, without
        waiting for it: a driver call can't be interrupted, and can take a
        long time. Check busy to know if a job is still running.
        """
        self.stopping.set()
        self.executor.shutdown(wait=False, cancel_futures=True)

    def driver_from_hostname(self, hostname):
        drivername = self.config['driver']
        driver = PDUDriver.select(drivername)(hostname, self.config)
        driver.configure_ports(self.config)
        return driver

    def get_ports_warning(self) -> Optional[str]:
        """Return a warning if the driver doesn't know which ports the PDU has,
        or None if it does.
        """
        if self.driver.get_ports():
            return None
        return "Ports unknown, set port_count or port_names in the driver or config"

    def _run_with_retries(self, port, request, action):
        self.logger.info("Processing job for PDU %s: (%s %s)", self.hostname, request, port)
        retries = self.retries
        while retries > 0 and not self.stopping.is_set():
            try:
                self.busy = True
                result = action()
                self.driver._cleanup()  # pylint: disable=W0212
                return result
            except UnknownCommandException:
                # the driver can't handle the request, retrying won't help
                self.logger.warn("Driver cannot execute job: {} {}".format(port, request))
                raise
            except (OSError, pexpect.exceptions.EOF, Exception):  # pylint: disable=broad-except
                self.logger.warn(traceback.format_exc())
                self.logger.warn("Failed to execute job: {} {} (attempts left {})".format(port, request, retries - 1))
                if self.driver:
                    self.driver._bombout()  # pylint: disable=W0212,E1101
                self.stopping.wait(self.retrydelay)
                retries -= 1
                continue
            finally:
                self.busy = False
        if self.stopping.is_set():
            raise FailedRequestException(
                "Failed to {} port {} on PDU {}, shutting down".format(request, port, self.hostname)
            )
        raise FailedRequestException(
            "Failed to {} port {} on PDU {} after {} retries".format(request, port, self.hostname, self.retries)
        )

    def _check_port(self, port) -> str:
        """Return the port as a string to pass to the driver. Raises
        FailedRequestException if the port isn't one of the ports of the PDU.
        """
        try:
            port = self.driver.check_port(port)
        except FailedRequestException as e:
            raise FailedRequestException("{} of PDU {}".format(e, self.hostname))
        if not self.driver.get_ports():
            self.logger.warning("Can't check port %s is valid, the ports of PDU %s are unknown", port, self.hostname)
        return port

    def port_on(self, port):
        port = self._check_port(port)
        self._run_with_retries(port, "on", lambda: self.driver.port_on(port))
        self._set_cached_port_state(port, True)

    def port_off(self, port):
        port = self._check_port(port)
        self._run_with_retries(port, "off", lambda: self.driver.port_off(port))
        self._set_cached_port_state(port, False)

    def get_port_state(self, port) -> bool:
        """Query the PDU for the state of the port and cache the result.
        Returns True if the port is powered on, False if powered off.
        """
        port = self._check_port(port)
        on = self._run_with_retries(port, "get-port-state", lambda: self.driver.get_port_state(port))
        self._set_cached_port_state(port, on)
        return on

    def get_cached_port_state(self, port) -> Optional[bool]:
        """Return the last known state of the port without querying the PDU,
        or None if it is unknown.
        """
        return self.port_state_cache.get(str(port))

    def get_cached_port_states(self) -> dict:
        """Return the last known state of every port with a known state,
        keyed by str(port), without querying the PDU.
        """
        return dict(self.port_state_cache)

    def get_port_state_change_times(self) -> dict:
        """Return the time.time() the cached state of every port with a known
        state last changed, keyed by str(port). Setting the same state again,
        e.g. switching on a port which is already on, isn't a change.
        """
        return dict(self.port_state_changed)

    def _set_cached_port_state(self, port, on: bool):
        """Cache the new state of a port."""
        port = str(port)
        if self.port_state_cache.get(port) != on:
            self.port_state_changed[port] = time.time()
        self.port_state_cache[port] = on

    async def _in_executor(self, fn, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, fn, *args)

    async def port_on_async(self, port) -> None:
        await self._in_executor(self.port_on, port)

    async def port_off_async(self, port) -> None:
        await self._in_executor(self.port_off, port)

    async def get_port_state_async(self, port) -> bool:
        return await self._in_executor(self.get_port_state, port)
