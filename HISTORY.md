This project has history of over 18 years spanning back to Python 1.5

There have been a number of people who have worked on this. I am awed
by the amount of work, number of people who have contributed to this,
and the cleverness in the code.

The below is an annotated history from talking to participants
involved and my reading of the code and sources cited.

In 1998, John Aycock first wrote a grammar parser in Python,
eventually called SPARK, that was usable inside a Python program. This
code was described in the
[7th International Python Conference](http://legacy.python.org/workshops/1998-11/proceedings/papers/aycock-little/aycock-little.html). That
paper doesn't talk about decompilation, nor did John have that in mind
at that time. It does mention that a full parser for Python (rather
than the simple languages in the paper) was being considered.

[This](http://pages.cpsc.ucalgary.ca/~aycock/spark/content.html#contributors)
contains a of people acknowledged in developing SPARK. What's amazing
about this code is that it is reasonably fast and has survived up to
Python 3 with relatively little change. This work was done in
conjunction with his Ph.D Thesis. This was finished around 2001. In
working on his thesis, John realized SPARK could be used to deparse
Python bytecode. In the fall of 1999, he started writing the Python
program, "decompyle", to do this.

To help with control structure deparsing the instruction sequence was
augmented with pseudo instruction COME_FROM. This code introduced
another clever idea: using table-driven semantics routines, using
format specifiers.

The last mention of a release of SPARK from John is around 2002. As
released, although the Earley Algorithm parser was in good shape, this
code was woefully lacking as serious Python deparser.

In the fall of 2000, Hartmut Goebel
[took over maintaining the code](https://groups.google.com/forum/#!searchin/comp.lang.python/hartmut$20goebel/comp.lang.python/35s3mp4-nuY/UZALti6ujnQJ). The
first subsequent public release announcement that I can find is
["decompyle - A byte-code-decompiler version 2.2 beta 1"](https://mail.python.org/pipermail/python-announce-list/2002-February/001272.html).

From the CHANGES file found in
[the tarball for that release](http://old-releases.ubuntu.com/ubuntu/pool/universe/d/decompyle2.2/decompyle2.2_2.2beta1.orig.tar.gz),
it appears that Hartmut did most of the work to get this code to
accept the full Python language. He added precedence to the table
specifiers, support for multiple versions of Python, the
pretty-printing of docstrings, lists, and hashes. He also wrote test and verification routines of
deparsed bytecode, and used this in an extensive set of tests that he also wrote. He says he could verify against the
entire Python library. However I have subsequently found small and relatively obscure bugs in the decompilation code.

decompyle2.2 was packaged for Debian (sarge) by
[Ben Burton around 2002](https://packages.qa.debian.org/d/decompyle.html). As
it worked on Python 2.2 only long after Python 2.3 and 2.4 were in
widespread use, it was removed.

[Crazy Compilers](http://www.crazy-compilers.com/decompyle/) offers a
byte-code decompiler service for versions of Python up to 2.6. As
someone who worked in compilers, it is tough to make a living by
working on compilers. (For example, based on
[John Aycock's recent papers](http://pages.cpsc.ucalgary.ca/~aycock/)
it doesn't look like he's done anything compiler-wise since SPARK). So
I hope people will use the crazy-compilers service. I wish them the
success that his good work deserves.

Dan Pascu did a bit of work from late 2004 to early 2006 to get this
code to handle first Python 2.3 and then 2.4 bytecodes. Because of
jump optimization introduced in the CPython bytecode compiler at that
time, various JUMP instructions were classified to assist parsing For
example, due to the way that code generation and line number table
work, jump instructions to an earlier offset must be looping jumps,
such as those found in a "continue" statement; "COME FROM"
instructions were reintroduced.  See
[RELEASE-2.4-CHANGELOG.txt](https://github.com/rocky/python-uncompyle6/blob/master/DECOMPYLE-2.4-CHANGELOG.txt)
for more details here. There wasn't a public release of RELEASE-2.4
and bytecodes other than Python 2.4 weren't supported. Dan says the
Python 2.3 version could verify the entire Python library. But given
subsequent bugs found like simply recognizing complex-number constants
in bytecode, decompilation wasn't perfect.

Next we get to ["uncompyle" and
PyPI](https://pypi.python.org/pypi/uncompyle/1.1) and the era of
public version control. (Dan's code although not public used
[darcs](http://darcs.net/) for version control.)

In contrast to _decompyle_, _uncompyle_ at least in its final versions,
runs only on Python 2.7. However it accepts bytecode back to Python
2.5. Thomas Grainger is the package owner of this, although Hartmut is
still listed as the author.

The project exists not only on
[github](https://github.com/gstarnberger/uncompyle) but also on
[bitbucket](https://bitbucket.org/gstarnberger/uncompyle) and later
the defunct [google
code](https://code.google.com/archive/p/unpyc/). The git/svn history
goes back to 2009. Somewhere in there the name was changed from
"decompyle" to "unpyc" by Keknehv, and then to "uncompyle" by Guenther Starnberger.

The name Thomas Grainger isn't found in (m)any of the commits in the
several years of active development. First Keknehv worked on this up
to Python 2.5 or so while acceping Python bytecode back to 2.0 or
so. Then hamled made a few commits earler on, while Eike Siewertsen
made a few commits later on. But mostly wibiti, and Guenther
Starnberger got the code to where uncompyle2 was around 2012.

While John Aycock and Hartmut Goebel were well versed in compiler
technology, those that have come afterwards don't seem to have been as
facile in it.  Furthermore, documentation or guidance on how the
decompiler code worked, comparison to a conventional compiler
pipeline, how to add new constructs, or debug grammars was weak. Some
of the grammar tracing and error reporting was a bit weak as well.

Given this, perhaps it is not surprising that subsequent changes
tended to shy away from using the built-in compiler technology
mechanisms and addressed problems and extensions by some other means.

Specifically, in `uncompyle`, decompilation of python bytecode 2.5 &
2.6 is done by transforming the byte code into a pseudo-2.7 Python
bytecode and is based on code from Eloi Vanderbeken. A bit of this
could have bene easily added by modifying grammar rules.

This project, `uncompyle6`, abandons that approach for various
reasons. Having a grammar per Python version is much cleaner and it
scales indefinitely. That said, we don't have entire copies of the
grammar, but work off of differences from some neighboring version.

Should there be a desire to rebase or start a new base version to work
off of, say for some future Python version, that can be done by
dumping a grammar for a specific version after it has been loaded
incrementally. You can get a full dump of the grammar by profiling the
grammar on a large body of Python source code.

Another problem with pseudo-2.7 bytecode is that that we need offsets
in fragment deparsing to be exactly the same as the bytecode; the
transformation process can remove instructions.  _Adding_ instructions
with psuedo offsets is however okay.

`Uncompyle6` however owes its existence to the fork of `uncompyle2` by
Myst herie (Mysterie) whose first commit picks up at
2012. I chose this since it seemed to have been at that time the most
actively, if briefly, worked on. Also starting around 2012 is Dark
Fenx's uncompyle3 which I used for inspiration for Python3 support.

I started working on this late 2015, mostly to add fragment support.
In that, I decided to make this runnable on Python 3.2+ and Python 2.6+
while, handling Python bytecodes from Python versions 2.5+ and
3.2+. In doing so, it has been expedient to separate this into three
projects:

* marshaling/unmarshaling, bytecode loading and disassembly ([xdis](https://pypi.python.org/pypi/xdis)),
* parsing and tree building ([spark_parser](https://pypi.python.org/pypi/spark_parser)),
* this project - grammar and semantic actions for decompiling
  ([uncompyle6](https://pypi.python.org/pypi/uncompyle6)).


Over the many years, code styles and Python features have
changed. However brilliant the code was and still is, it hasn't really
had a single public active maintainer. And there have been many forks
of the code.  I have spent a great deal of time trying to organize and
modularize the code so that it can handle more Python versions more
gracefully (with still only moderate success).

That it has been in need of an overhaul has been recognized by the
Hartmut a decade an a half ago:

[decompyle/uncompile__init__.py](https://github.com/gstarnberger/uncompyle/blob/master/uncompyle/__init__.py#L25-L26)

    NB. This is not a masterpiece of software, but became more like a hack.
    Probably a complete rewrite would be sensefull. hG/2000-12-27

This project deparses using an Earley-algorithm parse with lots of
massaging of tokens and the grammar in the scanner
phase. Earley-algorithm parsers are context free and tend to be linear
if the grammar is LR or left recursive. There is a technique for
improving LL right recursion, but our parser doesn't have that yet.

Another approach to decompiling, and one that doesn't use grammars is
to do something like simulate execution symbolically and build
expression trees off of stack results. Control flow in that approach
still needs to be handled somewhat ad hoc.  The two important projects
that work this way are [unpyc3](https://code.google.com/p/unpyc3/) and
most especially [pycdc](https://github.com/zrax/pycdc) The latter
project is largely by Michael Hansen and Darryl Pogue. If they
supported getting source-code fragments, did a better job in
supporting Python more fully, and had a way I could call it from
Python, I'd probably would have ditched this and used that. The code
runs blindingly fast and spans all versions of Python, although more
recently Python 3 support has been lagging. The code is impressive for
its smallness given that it covers many versions of Python. However, I
think it has reached a scalability issue, same as all the other
efforts. To handle Python versions more accurately, I think that code
base will need to have a lot more code specially which specializes for
Python versions. And then it will run into a modularity problem.

Tests for the project have been, or are being, culled from all of the
projects mentioned. Quite a few have been added to improve grammar
coverage and to address the numerous bugs that have been encountered.

If you think, as I am sure will happen in the future, "hey, I can just
write a decompiler from scratch and not have to deal with all all of
the complexity here", think again. What is likely to happen is that
you'll get at best a 90% solution working for a single Python release
that will be obsolete in about a year, and more obsolete each
subsequent year.  Writing a decompiler for Python gets harder as it
Python progresses, so writing one for Python 3.7 isn't as easy as it
was for Python 2.2.  That said, if you still feel you want to write a
single version decompiler, look at the test cases in this project and
talk to me. I may have some ideas.


For a little bit of the history of changes to the Earley-algorithm parser,
see the file [NEW-FEATURES.rst](https://github.com/rocky/python-spark/blob/master/NEW-FEATURES.rst) in the [python-spark github repository](https://github.com/rocky/python-spark).

NB. If you find mistakes, want corrections, or want your name added
(or removed), please contact me.
