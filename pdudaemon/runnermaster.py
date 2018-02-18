#! /usr/bin/python

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

import pdudaemon.pdurunner as pdurunner
from multiprocessing import Process
from setproctitle import setproctitle  # pylint: disable=no-name-in-module
from pdudaemon.shared import pdus_from_config
import signal
import sys
import os
import logging
processes = []
log = logging.getLogger(__name__)


def start_runner(config, pdu):
    setproctitle("pdurunner for %s" % pdu)
    p = pdurunner.PDURunner(config, pdu)
    p.run_me()


def start_em_up(config):
    pdus = pdus_from_config(config)
    for pdu in pdus:
        p = Process(target=start_runner, args=(config, pdu))
        p.start()
        processes.append(p)
    signal.signal(signal.SIGTERM, signal_term_handler)

def signal_term_handler(a, b):
    del a, b
    print 'Sending sigterm to all children'
    for proc in processes:
        log.debug("Terminate %s", proc.pid)
        proc.terminate()
        proc.join()
    sys.exit(0)
