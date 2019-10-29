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
import contextlib
import json
import logging
from logging.handlers import WatchedFileHandler
from queue import Empty, Queue
import signal
import sqlite3
import sys
import time

from pdudaemon.tcplistener import TCPListener
from pdudaemon.httplistener import HTTPListener
from pdudaemon.pdurunner import PDURunner
from pdudaemon.drivers.driver import PDUDriver


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


def setup_logging(options):
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
    options.loglevel = options.loglevel.upper()
    if options.loglevel == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif options.loglevel == "INFO":
        logger.setLevel(logging.INFO)
    elif options.loglevel == "WARNING":
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.ERROR)


class TasksDB(object):
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "hostname TEXT, port INTEGER, request TEXT, exectime INTEGER)")
        self.conn.commit()

    def create(self, hostname, port, request, exectime):
        try:
            self.conn.execute("INSERT INTO tasks (hostname, port, request, exectime) VALUES(?, ?, ?, ?)",
                              (hostname, port, request, int(exectime)))
            self.conn.commit()
            return 0
        except sqlite3.Error:
            return 1

    def delete(self, task_id):
        with contextlib.suppress(sqlite3.Error):
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id, ))
            self.conn.commit()

    def next(self, hostname):
        row = self.conn.execute("SELECT * FROM tasks WHERE hostname=? AND exectime < ? ORDER BY id ASC LIMIT 1", (hostname, int(time.time()))).fetchone()
        return row


def main():
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
    parser.add_argument("--dbfile", "-d", type=str,
                        help="SQLite3 db file")
    parser.add_argument("--listener", type=str, help="PDUDaemon listener setting")
    conflict = parser.add_mutually_exclusive_group()
    conflict.add_argument("--alias", dest="alias", action="store", type=str)
    conflict.add_argument("--hostname", dest="drivehostname", action="store", type=str)
    drive = parser.add_argument_group("drive")
    drive.add_argument("--drive", action="store_true", default=False)
    drive.add_argument("--request", dest="driverequest", action="store", type=str)
    drive.add_argument("--retries", dest="driveretries", action="store", type=int, default=5)
    drive.add_argument("--port", dest="driveport", action="store", type=int)

    # Parse the command line
    options = parser.parse_args()

    # Setup logging
    setup_logging(options)

    # Read the configuration file
    try:
        settings = json.loads(options.conf.read())
    except Exception as exc:
        logging.error("Unable to read configuration file '%s': %s", options.conf.name, exc)
        return 1
    dbfile = options.dbfile if options.dbfile else settings['daemon']['dbname']

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

        task_queue = Queue()
        runner = PDURunner(config, options.drivehostname, task_queue, options.driveretries)
        if options.driverequest == "reboot":
            result = runner.do_job(options.driveport, "off")
            result = runner.do_job(options.driveport, "on")
        else:
            result = runner.do_job(options.driveport, options.driverequest)
        # currently the drivers dont all reply with a result, so just exit(0) for now
        sys.exit(0)

    logger.info('PDUDaemon starting up')

    # Context
    workers = {}
    db_queue = Queue()
    dbhandler = TasksDB(dbfile)

    # Starting the workers
    logger.info("Starting the Workers")
    for hostname in settings["pdus"]:
        config = settings["pdus"][hostname]
        retries = config.get("retries", 5)
        task_queue = Queue()
        workers[hostname] = {"thread": PDURunner(config, hostname, task_queue, retries), "queue": task_queue}
        workers[hostname]["thread"].start()

    # Start the listener
    logger.info("Starting the listener")
    if options.listener:
        listener = options.listener
    else:
        listener = settings['daemon'].get('listener', 'tcp')
    if listener == 'tcp':
        listener = TCPListener(settings, db_queue)
    elif listener == 'http':
        listener = HTTPListener(settings, db_queue)
    else:
        logging.error("Unknown listener configured")
    listener.start()

    # Setup signal handling
    def signal_handler(signum, frame):
        logger.info("Signal received, shutting down listener")
        listener.shutdown()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Main loop
    try:
        while True:
            with contextlib.suppress(Empty):
                while True:
                    task = db_queue.get_nowait()
                    action = task[0]
                    logger.debug("db actions %s", action)
                    if action == "CREATE":
                        ret = dbhandler.create(task[1], task[2], task[3], task[4])
                        logger.debug("ret=%d", ret)
                    elif action == "DELETE":
                        dbhandler.delete(task[1])

            for worker in workers:
                # Is the last task done
                if workers[worker]["queue"].empty():
                    task = dbhandler.next(worker)
                    if task is not None:
                        task_id = task["id"]
                        port = task["port"]
                        request = task["request"]
                        logger.debug("put for %s: '%s' to port %s [id:%s]", worker, request, port, task_id)
                        workers[worker]["queue"].put((task["port"], task["request"]))
                        dbhandler.delete(task["id"])
            # TODO: compute the timeout correctly
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Waiting for workers to finish...")
        for worker in workers:
            workers[worker]["queue"].put(None)
            workers[worker]["thread"].join()
        sys.exit()
    return 0


if __name__ == "__main__":
    # execute only if run as a script
    main()
