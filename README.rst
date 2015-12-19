uncompyle6
==========

A native Python Byte-code Disassembler, Decompiler, and byte-code library


Introduction
------------

*uncompyle6* translates Python byte-code back into equivalent Python
source code. It accepts byte-codes from Python version 2.5 to 2.7, and
runs on Python 2.6 and 2.7 and Python 3.4.

Why this?
---------

What makes this different other CPython byte-code decompilers?  Its
ability to deparse just fragments and give source-code information
around a given bytecode offset.

I using this to deparse fragments of code inside my trepan_
debuggers_. For that, I need to record text fragements for all
byte-code offsets (of interest). This purpose although largely
compatible with the original intention is yet a little bit different.
See [this](https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting) for more information.

This library though could be used in showing stack traces or any
program that wants to show a location in more detail than just a line
number.  In fact it can be used when when source-code information does
exist and there is just bytecode information.


Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    python setup.py install # may need sudo
    # or if you have pyenv:
    python setup.py develop

A GNU makefile is also provided so `make install` (possibly as root or
sudo) will do the steps above.

Testing
-------

::

   make check-2.7 # if running on Python 2.7
   make check-3.4 # if running on Pyton 3.4

Testing right now is largely via utility `test/test_pythonlib.py`.  A
GNU makefile has been added to smooth over setting running the right
command. If you have remake_ installed, you can see the list of all
tasks including tests via `remake --tasks`


Usage
-----

Run

::

     ./bin/uncompyle6 -h
     ./bin/pydisassemble -y

for usage help


Known Bugs/Restrictions
-----------------------

Support Python 3 bytecode and syntax is lacking.

See Also
--------

https://github.com/zrax/pycdc


.. _trepan: https://pypi.python.org/pypi/trepan
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
