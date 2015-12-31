|buildstatus|

uncompyle6
==========

A native Python Byte-code Disassembler, Decompiler, Fragment Decompiler
and byte-code library


Introduction
------------

*uncompyle6* translates Python byte-code back into equivalent Python
source code. It accepts byte-codes from Python version 2.5 to 3.4 or
so and has been tested on Python running versions 2.6, 2.7, 3.3,
3.4 and 3.5.

Why this?
---------

What makes this different other CPython byte-code decompilers?  Its
ability to deparse just fragments and give source-code information
around a given bytecode offset.

I using this to deparse fragments of code inside my trepan_
debuggers_. For that, I need to record text fragments for all
byte-code offsets (of interest). This purpose although largely
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
the bytecode using version of Python different from the one used to
compile the bytecode.


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
     ./bin/pydisassemble -y

for usage help


Known Bugs/Restrictions
-----------------------

Python 2 deparsing is probably as solid as the various versions of
uncompyle2.  Python 3 deparsing is okay but not as solid.

See Also
--------

* https://github.com/zrax/pycdc
* https://github.com/Mysterie/uncompyle2
* https://github.com/DarkFenX/uncompyle3
* https://code.google.com/p/unpyc3/

The HISTORY file.

.. _trepan: https://pypi.python.org/pypi/trepan
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
.. _this: https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
.. |buildstatus| image:: https://travis-ci.org/rocky/python-uncompyle6.svg
		 :target: https://travis-ci.org/rocky/python-uncompyle6
