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

from setuptools import setup

# grab metadata without importing the module
metadata = {}
with open("pdudaemon/__about__.py", encoding="utf-8") as fp:
    exec(fp.read(), metadata)

# Setup the package
setup(
    name='pdudaemon',
    version=metadata['__version__'],
    description=metadata['__description__'],
    author=metadata['__author__'],
    author_email='matt@mattface.org',
    license=metadata['__license__'],
    url=metadata['__url__'],
    python_requires=">=3.4",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Networking",
    ],
    packages=['pdudaemon', 'pdudaemon.drivers'],
    entry_points={
        'console_scripts': [
            'pdudaemon = pdudaemon:main'
        ]
    },
    install_requires=[
        "aiohttp",
        "requests",
        "pexpect",
        "systemd_python",
        "paramiko",
        "pyserial",
        "hidapi",
        "pysnmp",
        "pyasn1",
        "pyusb",
        "pymodbus",
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-mock',
        ],
    },
    zip_safe=True
)
