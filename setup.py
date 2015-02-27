#! /usr/bin/env python
#
# Copyright (C) 2013 Linaro Limited
#
# Author: Matthew Hart <matthew.hart@linaro.org>
#
# This file is part of PDUDAEMON.
#
# PDUDAEMON is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PDUDAEMON is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses>.

from setuptools import setup, find_packages

setup(
    name='lavapdu',
    version="0.0.4",
    author="Matthew Hart",
    author_email="matthew.hart@linaro.org",
    license="GPL2+",
    description="LAVA PDU Deamon for APC PDU's",
    packages=find_packages(),
    install_requires=[
        "daemon",
        "lockfile",
        "pexpect",
        "psycopg2"
    ],
    data_files=[
        ("/etc/init.d/", ["etc/lavapdu-runner.init"]),
        ("/etc/init.d/", ["etc/lavapdu-listen.init"]),
        ("/etc/", ["etc/lavapdu.conf"]),
        ("/etc/logrotate.d/", ["etc/lavapdulogrotate"]),
    ],
    scripts=[
        'lavapdu-runner',
        'lavapdu-listen',
        'pduclient'
    ],
    zip_safe=False,
    include_package_data=True)
