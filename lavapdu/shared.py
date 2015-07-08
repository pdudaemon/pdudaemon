import logging
import json
from logging.handlers import WatchedFileHandler


def getDaemonLogger(filePath, log_format=None, loglevel=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    try:
        watchedHandler = WatchedFileHandler(filePath)
    except Exception as e:
        return e

    watchedHandler.setFormatter(logging.Formatter(log_format or '%(asctime)s %(msg)s'))
    logger.addHandler(watchedHandler)
    return logger, watchedHandler


def readSettings(filename):
    """
    Read settings from config file, to listen to all hosts, hostname should be 0.0.0.0
    """
    #settings = {}
    print("Reading settings from %s" % filename)
    with open(filename) as stream:
        jobdata = stream.read()
        json_data = json.loads(jobdata)
    return json_data

def drivername_from_hostname(hostname, pdus):
    if hostname in pdus:
        drivername = (pdus[hostname]["driver"])
    else:
        raise NotImplementedError("No configuration available for hostname %s\n"
                                  "Is there a section in the lavapdu.conf?" % hostname)
    return drivername
