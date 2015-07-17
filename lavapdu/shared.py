import logging
import json
from logging.handlers import WatchedFileHandler


def get_daemon_logger(filepath, log_format=None, loglevel=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    try:
        watchedhandler = WatchedFileHandler(filepath)
    except Exception as e:  # pylint: disable=broad-except
        return e

    watchedhandler.setFormatter(logging.Formatter(log_format
                                                  or '%(asctime)s %(msg)s'))
    logger.addHandler(watchedhandler)
    return logger, watchedhandler


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
