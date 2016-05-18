|buildstatus|

uncompyle6
==========

A native Python bytecode Disassembler, Decompiler, Fragment Decompiler
and bytecode library. Follows in the tradition of decompyle, uncompyle, and uncompyle2.


Introduction
------------

*uncompyle6* translates Python bytecode back into equivalent Python
source code. It accepts bytecodes from Python version 2.5 to 3.5 or
so. The code requires Python 2.6 or later and has been tested on Python
running versions 2.6, 2.7, 3.2, 3.3, 3.4 and 3.5.

Why this?
---------

There were a number of decompyle, uncompile, uncompyle2, uncompyle3
forks around. All of them come basically from the same code base, and
almost all of them not maintained very well. This code pulls these together
and addresses a number of open issues in those.

What makes this different from other CPython bytecode decompilers?  Its
ability to deparse just fragments and give source-code information
around a given bytecode offset.

I use this to deparse fragments of code inside my trepan_
debuggers_. For that, I need to record text fragments for all
bytecode offsets (of interest). This purpose although largely
compatible with the original intention is yet a little bit different.
See this_ for more information.

The idea of Python fragment deparsing given an instruction offset can
be used in showing stack traces or any program that wants to show a
location in more detail than just a line number.  It can be also used
when source-code information does not exist and there is just bytecode
information.

Other parts of the library can be used inside Python for various
bytecode-related tasks. For example you can read in bytecode,
i.e. perform a version-independent `marshal.loads()`, and disassemble
the bytecode using a version of Python different from the one used to
compile the bytecode.


Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python setup.py install # may need sudo
    # or if you have pyenv:
    python setup.py develop

A GNU makefile is also provided so `make install` (possibly as root or
sudo) will do the steps above.

Testing
-------

::

   make check

A GNU makefile has been added to smooth over setting running the right
command, and running tests from fastest to slowest.

If you have remake_ installed, you can see the list of all tasks
including tests via `remake --tasks`


Usage
-----

Run

::

     ./bin/uncompyle6 -h
     ./bin/pydisassemble -h

for usage help.


Known Bugs/Restrictions
-----------------------

Python 2 deparsing decompiles about the first 140 or so of the Python
2.7.10 and 2.7.11 standard library files and all but less that 10%
verify. So as such, it is probably a little better than uncompyle2.
Other Python 2 versions do worse.

Python 3 deparsing before 3.5 is okay, but even there, more work is needed to
decompile all of its library. Python 3.5 is missing some of new
opcodes and idioms added, but it still often works.

There is lots to do, so please dig in and help.

See Also
--------

* https://github.com/zrax/pycdc : supports all versions of Python and is written in C++
* https://code.google.com/archive/p/unpyc3/ : supports Python 3.2 only

The above projects use a different decompiling technique what is used here.

The HISTORY file.

.. |downloads| image:: https://img.shields.io/pypi/dd/uncompyle6.svg
.. _trepan: https://pypi.python.org/pypi/trepan
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
.. _this: https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
.. |buildstatus| image:: https://travis-ci.org/rocky/python-uncompyle6.svg
		 :target: https://travis-ci.org/rocky/python-uncompyle6
