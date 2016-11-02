import os
import sys
import logging
import json
import argparse
from os.path import basename
from logging.handlers import WatchedFileHandler
from logging import StreamHandler

import daemon
try:
    import daemon.pidlockfile as pidlockfile
except ImportError:
    from lockfile import pidlockfile

def get_daemon_logger(filepath, log_format=None, loglevel=logging.INFO, journal=False):
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    try:
        if journal:
            from systemd.journal import JournalHandler
            handler = JournalHandler(SYSLOG_IDENTIFIER=basename(sys.argv[0]))
        elif filepath:
            handler = WatchedFileHandler(filepath)
        else:
            handler = StreamHandler()
    except Exception as e:  # pylint: disable=broad-except
        print("Fatal error creating client_logger: " + str(e))
        sys.exit(os.EX_OSERR)

    if (log_format):
        handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)
    return logger, handler


def read_settings(filename):
    with open(filename) as stream:
        jobdata = stream.read()
        json_data = json.loads(jobdata)
    return json_data


def drivername_from_hostname(hostname, pdus):
    if hostname in pdus:
        drivername = (pdus[hostname]["driver"])
    else:
        raise NotImplementedError("No configuration available for %s, "
                                  "is there a section in the lavapdu.conf?" %
                                  hostname)
    return drivername


def pdus_from_config(data):
    output = []
    for pdu in data["pdus"]:
        output.append(pdu)
    return output

def setup_daemon(options, settings, pidfile):
    logfile = options.logfile
    level = logging.DEBUG
    daemon_settings = settings["daemon"]
    if daemon_settings["logging_level"] == "DEBUG":
        level = logging.DEBUG
    if daemon_settings["logging_level"] == "WARNING":
        level = logging.WARNING
    if daemon_settings["logging_level"] == "ERROR":
        level = logging.ERROR
    if daemon_settings["logging_level"] == "INFO":
        level = logging.INFO
    client_logger, handler = get_daemon_logger(
        None if options.foreground else logfile,
        loglevel=level,
        log_format=None if options.journal
                        else '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        journal=options.journal)
    # noinspection PyArgumentList
    lockfile = pidlockfile.PIDLockFile(pidfile)
    if lockfile.is_locked():
        logging.error("PIDFile %s already locked" % pidfile)
        sys.exit(os.EX_OSERR)
    context = daemon.DaemonContext(
        detach_process=not options.foreground,
        working_directory=os.getcwd(),
        pidfile=lockfile,
        files_preserve=None if options.journal else [handler.stream],
        stderr=sys.stderr if options.journal else handler.stream,
        stdout=sys.stdout if options.journal else handler.stream)

    return context


def get_common_argparser(description, logfile):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--foreground", "-f",
                        help="Stay in the foreground",
                        action="store_true", default=False)
    parser.add_argument("--journal", "-j",
                        help="Log to the journal",
                        action="store_true", default=False)
    parser.add_argument("--logfile", dest="logfile", action="store",
                        type=str, default=logfile,
                        help="log file [%s]" % logfile)
    parser.add_argument("--loglevel", dest="loglevel", action="store",
                        type=str, help="logging level [INFO]")
    return parser

