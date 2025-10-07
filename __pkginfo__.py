# Copyright (C) 2018, 2020-2021 2024 Rocky Bernstein <rocky@gnu.org>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""uncompyle6 packaging information"""

# To the extent possible we make this file look more like a
# configuration file rather than code like setup.py. I find putting
# configuration stuff in the middle of a function call in setup.py,
# which for example requires commas in between parameters, is a little
# less elegant than having it here with reduced code, albeit there
# still is some room for improvement.

# Python-version | package | last-version |
# -----------------------------------------
# 2.5            | pip     |  1.1         |
# 2.6            | pip     |  1.5.6       |
# 2.7            | pip     | 19.2.3       |
# 2.7            | pip     |  1.2.1       |
# 3.1            | pip     |  1.5.6       |
# 3.2            | pip     |  7.1.2       |
# 3.3            | pip     | 10.0.1       |
# 3.4            | pip     | 19.1.1       |

import os.path as osp

# Things that change more often go here.
copyright = """
Copyright (C) 2015-2021, 2024 Rocky Bernstein <rb@dustyfeet.com>.
"""

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.4",
    "Programming Language :: Python :: 2.5",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Debuggers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# The rest in alphabetic order
author = "Rocky Bernstein, Hartmut Goebel, John Aycock, and others"
author_email = "rb@dustyfeet.com"
entry_points = {
    "console_scripts": [
        "uncompyle6=uncompyle6.bin.uncompile:main_bin",
        "pydisassemble=uncompyle6.bin.pydisassemble:main",
    ]
}
ftp_url = None
install_requires = ["click", "spark-parser >= 1.8.9, < 1.9.2", "xdis >= 6.1.1, < 6.2.0"]

license = "GPL3"
mailing_list = "python-debugger@googlegroups.com"
modname = "uncompyle6"
py_modules = None
short_desc = "Python cross-version byte-code decompiler"
web = "https://github.com/rocky/python-uncompyle6/"

# tracebacks in zip files are funky and not debuggable
zip_safe = True


def get_srcdir():
    filename = osp.normcase(osp.dirname(osp.abspath(__file__)))
    return osp.realpath(filename)


srcdir = get_srcdir()


def read(*rnames):
    return open(osp.join(srcdir, *rnames)).read()


# Get info from files; set: long_description and VERSION
long_description = read("README.rst") + "\n"

# The "exec" below rewrites __version__.
__version__="??"
exec(read("uncompyle6/version.py"))
