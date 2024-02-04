# Introduction

This project started around 1999 spanning back to Python 1.5

In the interest of shortening what is written here, I am going to start where we left off where [decompyle 2.4's history](https://github.com/rocky/decompile-2.4/blob/master/HISTORY.md) ends.

For the earlier history up to 2006 and the code up until Python 2.4, which I find interesting, look at that link.

Sometime around 2014 was the dawn of ["uncompyle" and PyPI](https://pypi.python.org/pypi/uncompyle/1.1) &mdash; the era of
public version control. Dan Pascu's code although not public used [darcs](http://darcs.net/) for version control. I converted the darcs repository to git and put this at [decompyle-2.4](https://github.com/rocky/decompile-2.4).

# uncompyle, unpyc

In contrast to _decompyle_ that went up to Python 2.4, _uncompyle_, at least in its final versions, runs only on Python 2.7. However it accepts bytecode back to Python 2.5. Thomas Grainger is the package owner of this, although Hartmut is still listed as the author.

The project exists not only on [github](https://github.com/gstarnberger/uncompyle) but also on
[bitbucket](https://bitbucket.org/gstarnberger/uncompyle) and later the defunct [google
code](https://code.google.com/archive/p/unpyc/) under the name _unpyc_. The git/svn history goes back to 2009. Somewhere in there the name was changed from "decompyle" to "unpyc" by Keknehv, and then to "uncompyle" by Guenther Starnberger.

The name Thomas Grainger isn't found in (m)any of the commits in the several years of active development. First Keknehv worked on this up to Python 2.5 or so while accepting Python bytecode back to 2.0 or so. Then "hamled" made a few commits earlier on, while Eike Siewertsen made a few commits later on. But mostly "wibiti", and Guenther Starnberger got the code to where uncompyle2 was around 2012.

While John Aycock and Hartmut Goebel were well versed in compiler technology, those that have come afterwards don't seem to have been as facile in it.  Furthermore, documentation or guidance on how the decompiler code worked, comparison to a conventional compiler pipeline, how to add new constructs, or debug grammars was weak. Some of the grammar tracing and error reporting was a bit weak as well.

Given this, perhaps it is not surprising that subsequent changes tended to shy away from using the built-in compiler technology mechanisms and addressed problems and extensions by some other means.

Specifically, in `uncompyle`, decompilation of python bytecode 2.5 & 2.6 is done by transforming the byte code into a pseudo-2.7 Python bytecode and is based on code from Eloi Vanderbeken. A bit of this could have been easily added by modifying grammar rules.


# uncompyle2, uncompyle3, uncompyle6

`Uncompyle6`, which I started in 2015, owes its existence to the fork of [uncompyle2](https://github.com/Mysterie/uncompyle2) by Myst herie (Mysterie) whose first commit picks up at 2012. I chose this since it seemed to have been at that time the most actively, if briefly, worked on. Also starting around 2012 is Dark Fenx's [uncompyle3](https://github.com/DarkFenX/uncompyle3) which I used for inspiration for Python3 support.

I started working on this late 2015, mostly to add fragment support. In that, I decided to make this runnable on Python 3.2+ and Python 2.6+ while handling Python bytecodes from Python versions 2.5+ and
3.2+. In doing so, it was expedient to separate this into three projects:

* marshaling/unmarshaling, bytecode loading and disassembly ([xdis](https://pypi.python.org/pypi/xdis)),
* parsing and tree building ([spark_parser](https://pypi.python.org/pypi/spark_parser)),
* this project - grammar and semantic actions for decompiling
  ([uncompyle6](https://pypi.python.org/pypi/uncompyle6)).

 `uncompyle6`, abandons the idea found in some 2.7 version of `uncompyle` that support Python 2.6 and 2.5 by trying to rewrite opcodes at the bytecode level.

Having a grammar per Python version is simpler to maintain, cleaner and it scales indefinitely.

Over the many years, code styles and Python features have changed. However brilliant the code was and still is, it hasn't really had a single public active maintainer. And there have been many forks of the code.

That this code has been in need of an overhaul has been recognized by the Hartmut more than two decades ago.

[decompyle/uncompile__init__.py](https://github.com/gstarnberger/uncompyle/blob/master/uncompyle/__init__.py#L25-L26)

    NB. This is not a masterpiece of software, but became more like a hack.
    Probably a complete rewrite would be sensefull. hG/2000-12-27

In 2021, I created three git branches in order to allow the decompiler to run on a wide variety of Python versions from 2.4 up to 3.10. (Note this doesn't mean we decompile these versions. In fact we decompile starting from Python 1.0 up to Python 3.8 and no later than that.)

Using the separate git branches allows me to continually improve the coding style and add feature support while still supporting older Pythons. Supporting older Pythons is nice (but not strictly necessary) when you want to debug decompilation on older Pythons.

I have spent a great deal of time trying to organize, modularize and even modernize the code so that it can handle more Python versions more gracefully (with still only moderate success).

Tests for the project have been, or are being, culled from all of the projects mentioned above or below. Quite a few have been added to improve grammar coverage and to address the numerous bugs that have been encountered.


# unpyc3 and pydc

Another approach to decompiling, and one that doesn't use grammars is to do something like simulate execution symbolically and build expression trees off of stack results. Control flow in that approach
still needs to be handled somewhat ad hoc.  The two important projects that work this way are [unpyc3](https://code.google.com/p/unpyc3/) and most especially [pycdc](https://github.com/zrax/pycdc) The latter
project is largely by Michael Hansen and Darryl Pogue. If they supported getting source-code fragments, did a better job in supporting Python more fully, and had a way I could call it from Python, I'd probably would have ditched this and used that. The code runs blindingly fast and spans all versions of Python, although more recently Python 3 support has been lagging. The code is impressive for its smallness given that it covers many versions of Python. However, I think it has reached a scalability issue, same as all the other efforts. To handle Python versions more accurately, I think that code base will need to have a lot more code specially which specializes for Python versions. And then it will run into a modularity problem.

# So you want to write a decompiler for Python?

If you think, as I am sure will happen in the future, "hey, I can just write a decompiler from scratch and not have to deal with all of the complexity in uncompyle6", think again. What is likely to happen is that you'll get at best a 90% solution working for a single Python release that will be obsolete in about a year, and more obsolete each subsequent year.

Writing a decompiler for Python gets harder as it Python progresses. Writing decompiler for Python 3.7 isn't as easy as it was for Python 2.2. For one thing, now that Python has a well-established AST, that opens another interface by which code can be improved.

In Python 3.10 I am seeing (for the first time?) bytecode getting moved around so that it is no longer the case that line numbers have to be strictly increasing as bytecode offsets increase. And I am seeing dead code appear as well.

That said, if you still feel you want to write a single version decompiler, look at the test cases in this project and talk to me. I may have some ideas that I haven't made public yet. See also what I've written about the on how this code works and on [decompilation in dynamic runtime languages](http://rocky.github.io/Deparsing-Paper.pdf) in general.



# Earley Algorithm Parser

This project deparses using an Earley-algorithm parse. But in order to do this accurately, the process of tokenization is a bit more involved in the scanner. We don't just disassemble bytecode and use the opcode name. That aspect hasn't changed from the very first decompilers. However understanding _what_ information needs to be made explicit and what pseudo instructions to add that accomplish this has taken some time to understand.

Earley-algorithm parsers have gotten negative press, most notably by the dragon book. Having used this a bit, I am convinced having a system that handles ambiguous grammars is the right thing to do and matches the problem well. In practice the speed of the parser isn't a problem when one understand what's up. And this has taken a little while to understand.
Earley-algorithm parsers for context free languages or languages that are to a large extent context free and tend to be linear and the grammar steers towards left recursive rules. There is a technique for improving LL right recursion, but our parser doesn't have that yet.

The [decompiling paper](http://rocky.github.io/Deparsing-Paper.pdf) discusses these aspects in a more detail.


For a little bit of the history of changes to the Earley-algorithm parser, see the file [NEW-FEATURES.rst](https://github.com/rocky/python-spark/blob/master/NEW-FEATURES.rst) in the [python-spark github repository](https://github.com/rocky/python-spark).

NB. If you find mistakes, want corrections, or want your name added (or removed), please contact me.
