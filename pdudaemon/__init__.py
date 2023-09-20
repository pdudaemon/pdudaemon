#!/usr/bin/python3
#
#  Copyright 2018 Remi Duraffort <remi.duraffort@linaro.org>
#                 Matt Hart <matt@mattface.org>
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

import argparse
import asyncio
import json
import logging
from logging.handlers import WatchedFileHandler
import signal
import sys

from pdudaemon.tcplistener import TCPListener
from pdudaemon.httplistener import HTTPListener
from pdudaemon.pdurunner import PDURunner
from pdudaemon.drivers.driver import PDUDriver

assert PDUDriver, "Imported for user convenience." # type: ignore[truthy-function]

###########
# Constants
###########
CONFIGURATION_FILE = "/etc/pdudaemon/pdudaemon.conf"
logging_FORMAT = "%(asctime)s - %(name)-30s - %(levelname)s %(message)s"
logging_FORMAT_JOURNAL = "%(name)s.%(levelname)s %(message)s"
logging_FILE = "/var/log/pdudaemon.log"

##################
# Global logger
##################
logger = logging.getLogger('pdud')


def setup_logging(options, settings):
    logger = logging.getLogger("pdud")
    """
    Setup the log handler and the log level
    """
    if options.journal:
        from systemd.journal import JournalHandler
        handler = JournalHandler(SYSLOG_IDENTIFIER="pdudaemon")
        handler.setFormatter(logging.Formatter(logging_FORMAT_JOURNAL))
    elif options.logfile == "-" or not options.logfile:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(logging_FORMAT))
    else:
        handler = WatchedFileHandler(options.logfile)
        handler.setFormatter(logging.Formatter(logging_FORMAT))

    logger.addHandler(handler)
    settings_level = settings.get('daemon', {}).get('logging_level', None)
    if settings_level:
        options.loglevel = settings_level.upper()
    else:
        options.loglevel = options.loglevel.upper()
    if options.loglevel == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif options.loglevel == "INFO":
        logger.setLevel(logging.INFO)
    elif options.loglevel == "WARNING":
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.ERROR)


class PDUDaemon:
    def __init__(self, options, settings):
        # Context
        self.runners = {}

        # Create the runners
        logger.info("Creating the runners")
        for hostname in settings["pdus"]:
            config = settings["pdus"][hostname]
            retries = config.get("retries", 5)
            self.runners[hostname] = PDURunner(config, hostname, retries)

        # Start the listener
        logger.info("Starting the listener")
        if options.listener:
            listener = options.listener
        else:
            listener = settings['daemon'].get('listener', 'tcp')
        if listener == 'tcp':
            self.listener = TCPListener(settings, self)
        elif listener == 'http':
            self.listener = HTTPListener(settings, self)
        else:
            logging.error("Unknown listener configured")

    async def start(self):
        await self.listener.start()

    async def shutdown(self):
        logger.info("Shutting down listener...")
        await self.listener.shutdown()
        logger.info("Shutting down runners...")
        for runner in self.runners.values():
            await runner.shutdown()
        logger.info("Stopping loop...")
        loop = asyncio.get_running_loop()
        loop.stop()


async def main_async():
    # Setup the parser
    parser = argparse.ArgumentParser()

    log = parser.add_argument_group("logging")
    log.add_argument("--journal", "-j", action="store_true", default=False,
                     help="Log to the journal")
    log.add_argument("--logfile", dest="logfile", action="store", type=str,
                     default="-", help="log file [%s]" % logging_FILE)
    log.add_argument("--loglevel", dest="loglevel", default="INFO",
                     choices=["DEBUG", "ERROR", "INFO", "WARN"],
                     type=str, help="logging level [INFO]")
    parser.add_argument("--conf", "-c", type=argparse.FileType("r"),
                        default=CONFIGURATION_FILE,
                        help="configuration file [%s]" % CONFIGURATION_FILE)
    parser.add_argument("--listener", type=str, help="PDUDaemon listener setting")
    conflict = parser.add_mutually_exclusive_group()
    conflict.add_argument("--alias", dest="alias", action="store", type=str)
    conflict.add_argument("--hostname", dest="drivehostname", action="store", type=str)
    drive = parser.add_argument_group("drive")
    drive.add_argument("--drive", action="store_true", default=False)
    drive.add_argument("--request", dest="driverequest", action="store", type=str)
    drive.add_argument("--retries", dest="driveretries", action="store", type=int, default=5)
    drive.add_argument("--delay", dest="drivedelay", action="store", type=int, default=5)
    drive.add_argument("--port", dest="driveport", action="store", type=str)

    # Parse the command line
    options = parser.parse_args()

    # Read the configuration file
    try:
        settings = json.loads(options.conf.read())
    except Exception as exc:
        logging.error("Unable to read configuration file '%s': %s", options.conf.name, exc)
        return 1

    # Setup logging
    setup_logging(options, settings)

    # Get handle to the currently running loop
    loop = asyncio.get_running_loop()

    if options.drive:
        # Driving a PDU directly, dont start any Listeners

        if options.alias:
            # Using alias support, get all pdu info from alias
            alias_settings = settings["aliases"].get(options.alias, False)
            if not alias_settings:
                logging.error("Alias requested but not found")
                sys.exit(1)
            options.drivehostname = settings["aliases"][options.alias]["hostname"]
            options.driveport = settings["aliases"][options.alias]["port"]

        # Check that the requested PDU has config
        config = settings["pdus"].get(options.drivehostname, False)
        if not config:
            logging.error("No config section for hostname: {}".format(options.drivehostname))
            sys.exit(1)

        runner = PDURunner(config, options.drivehostname, options.driveretries)
        if options.driverequest == "reboot":
            result = await runner.do_job_async(options.driveport, "off")
            await asyncio.sleep(int(options.drivedelay))
            result = await runner.do_job_async(options.driveport, "on")
        else:
            result = await runner.do_job_async(options.driveport, options.driverequest)
        await runner.shutdown()
        loop.stop()
        return result

    # Create daemon
    logger.info('PDUDaemon starting up')
    daemon = PDUDaemon(options, settings)

    # Setup signal handling
    def cleanup_handler():
        logger.info("Signal received, shutting down...")
        asyncio.create_task(daemon.shutdown())

    loop.add_signal_handler(signal.SIGINT, cleanup_handler)
    loop.add_signal_handler(signal.SIGTERM, cleanup_handler)

    await daemon.start()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    # execute only if run as a script
    result = main()
    sys.exit(result)
