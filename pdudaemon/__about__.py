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

__all__ = ["__author__", "__description__", "__license__", "__url__",
           "__version__"]


def git_hash():
    import subprocess
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                      stderr=subprocess.STDOUT)
        return out.decode("utf-8").rstrip("\n")
    except Exception:
        return "git"


__author__ = "Matt Hart"
__description__ = 'Control and Queueing daemon for PDUs'
__license__ = 'GPLv2+'
__url__ = 'https://github.com/pdudaemon/pdudaemon.git'
__version__ = "0.1"
