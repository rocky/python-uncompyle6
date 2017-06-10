|buildstatus| |Supported Python Versions|

uncompyle6
==========

A native Python cross-version Decompiler and Fragment Decompiler.
Follows in the tradition of decompyle, uncompyle, and uncompyle2.


Introduction
------------

*uncompyle6* translates Python bytecode back into equivalent Python
source code. It accepts bytecodes from Python version 1.5, and 2.1 to
3.6 or so, including PyPy bytecode and Dropbox's Python 2.5 bytecode.

Why this?
---------

There were a number of decompyle, uncompile, uncompyle2, uncompyle3
forks around. All of them came basically from the same code base, and
almost all of them no were no longer actively maintained. Only one
handled Python 3, and even there, only 3.2 or 3.3 depending on which
code is used. This code pulls these together and moves forward. This
project has the most complete support for Python 3.3 and above. It
also addresses a number of open issues in the previous forks.

What makes this different from other CPython bytecode decompilers?: its
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

Requirements
------------

This project requires Python 2.6 or later, PyPy 3-2.4, or PyPy-5.0.1.
Python versions 2.4-2.7 are supported in the python-2.4 branch.
The bytecode files it can read has been tested on Python bytecodes from
versions 1.5, 2.1-2.7, and 3.0-3.6 and the above-mentioned PyPy versions.

Installation
------------

This uses setup.py, so it follows the standard Python routine:

::

    pip install -e .
    pip install -r requirements-dev.txt
    python setup.py install # may need sudo
    # or if you have pyenv:
    python setup.py develop

A GNU makefile is also provided so :code:`make install` (possibly as root or
sudo) will do the steps above.

Testing
-------

::

   make check

A GNU makefile has been added to smooth over setting running the right
command, and running tests from fastest to slowest.

If you have remake_ installed, you can see the list of all tasks
including tests via :code:`remake --tasks`


Usage
-----

Run

::

$ uncompyle6 *compiled-python-file-pyc-or-pyo*

For usage help:

::

   $ uncompyle6 -h

If you want strong verification of the correctness of the
decompilation process, add the `--verify` option. But there are
situations where this will indicate a failure, although the generated
program is semantically equivalent. Using option `--weak-verify` will
tell you if there is something definitely wrong. Generally, large
swaths of code are decompiled correctly, if not the entire program.

You can also cross compare the results with pycdc_ . Since they work
differently, bugs here often aren't in that, and vice versa.


Known Bugs/Restrictions
-----------------------

The biggest known and possibly fixable (but hard) problem has to do
with handling control flow. All of the Python decompilers I have looked
at have the same problem. In some cases we can detect an erroneous
decompilation and report that.

Over 98% of the decompilation of Python standard library packages in
Python 2.7.12 verifies correctly. Over 99% of Python 2.7 and 3.3-3.5
"weakly" verify. Python 2.6 drops down to 96% weakly verifying.
Other versions drop off in quality too.

*Verification* is the process of decompiling bytecode, compiling with
a Python for that bytecode version, and then comparing the bytecode
produced by the decompiled/compiled program. Some allowance is made
for inessential differences. But other semantically equivalent
differences are not caught. For example ``1 and 0`` is decompiled to
the equivalent ``0``; remnants of the first true evaluation (1) is
lost when Python compiles this. When Python next compiles ``0`` the
resulting code is simpler.

*Weak Verification*
on the other hand doesn't check bytecode for equivalence but does
check to see if the resulting decompiled source is a valid Python
program by running the Python interpreter. Because the Python language
has changed so much, for best results you should use the same Python
Version in checking as used in the bytecode.

Later distributions average about 200 files. There is some work to do
on the lower end Python versions which is more difficult for us to
handle since we don't have a Python interpreter for versions 1.5, 1.6,
and 2.0.

In the Python 3 series, Python support is is strongest around 3.4 or
3.3 and drops off as you move further away from those versions. Python
3.6 changes things drastically by using word codes rather than byte
codes. That has been addressed, but then it also changes function call
opcodes and its semantics and has more problems with control flow than
3.5 has.

Currently not all Python magic numbers are supported. Specifically in
some versions of Python, notably Python 3.6, the magic number has
changes several times within a version. We support only the released
magic. There are also customized Python interpreters, notably Dropbox,
which use their own magic and encrypt bytcode. With the exception of
the Dropbox's old Python 2.5 interpreter this kind of thing is not
handled.

We also don't handle PJOrion_ obfuscated code. For that try: PJOrion
Deobfuscator_ to unscramble the bytecode to get valid bytecode before
trying this tool.

Handling pathologically long lists of expressions or statements is
slow.


There is lots to do, so please dig in and help.

See Also
--------

* https://github.com/zrax/pycdc : supports all versions of Python and is written in C++. Support for later Python 3 versions is a bit lacking though.
* https://code.google.com/archive/p/unpyc3/ : supports Python 3.2 only. The above projects use a different decompiling technique than what is used here.
* https://github.com/figment/unpyc3/ : fork of above, but supports Python 3.3 only. Include some fixes like supporting function annotations
* The HISTORY_ file.
* `How to report a bug <https://github.com/rocky/python-uncompyle6/blob/master/HISTORY.md>`_
.. |downloads| image:: https://img.shields.io/pypi/dd/uncompyle6.svg
.. _trepan: https://pypi.python.org/pypi/trepan
.. _HISTORY: https://github.com/rocky/python-uncompyle6/blob/master/HISTORY.md
.. _debuggers: https://pypi.python.org/pypi/trepan3k
.. _remake: https://bashdb.sf.net/remake
.. _pycdc: https://github.com/zrax/pycdc
.. _this: https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
.. |buildstatus| image:: https://travis-ci.org/rocky/python-uncompyle6.svg
		 :target: https://travis-ci.org/rocky/python-uncompyle6
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/uncompyle6.svg
   :target: https://pypi.python.org/pypi/uncompyle6/
.. _PJOrion: http://www.koreanrandom.com/forum/topic/15280-pjorion-%D1%80%D0%B5%D0%B4%D0%B0%D0%BA%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%B4%D0%B5%D0%BA%D0%BE%D0%BC%D0%BF%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D1%8F-%D0%BE%D0%B1%D1%84
.. _Deobfuscator: https://github.com/extremecoders-re/PjOrion-Deobfuscator
