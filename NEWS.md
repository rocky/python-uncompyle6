3.7.4: 2020-8-05
================

* Fragment parsing was borked. This means deparsing in trepan2/trepan3k was broken
* 3.7+: narrow precedence for call tatement
* del_stmt -> delete to better match Python AST
* 3.8+ Add another `forelsestmt` (found only in a loop)
* 3.8+ Add precedence on walrus operator
* More files blackened
* bump min xdis version

3.7.3: 2020-7-25
================

Mostly small miscellaneous bug fixes

* `__doc__ = DocDescr()` from `test_descr.py` was getting confused as a docstring.
* detect 2.7 exchandler range better
* Add for .. else reduction checks on 2.6 and before
* Add reduce check for 2.7 augmented assign
* Add VERSION in a pydoc-friendly way


3.7.2: 2020-6-27
================

* Use newer xdis
* Docstrings (again) which were broken again on earlier Python
* Fix 2.6 and 2.7 decompilation bug in handling "list if" comprehensions



3.7.1: 2020-6-12 Fleetwood66
====================================================

Released to pick up new xdis version which has fixes to read bytestings better on 3.x

* Handle 3.7+ "else" branch removal adAs seen in `_cmp()` of `python3.8/distutils/version.py` with optimization `-O2`
* 3.6+ "with" and "with .. as" grammar improvements
* ast-check for "for" loop was missing some grammar rules

3.7.0: 2020-5-19 Primidi 1st Prairial - Alfalfa - HF
====================================================

The main impetus for this release is to pull in the recent changes from xdis.
We simplify imports using xdis 4.6.0.

There were some bugfixes to Python 3.4-3.8. See the ChangeLog for details


3.6.7: 2020-4-27 xdis again
===========================

More upheaval in xdis which we need to track here.

3.6.6: 2020-4-20 Love in the time of Cholera
============================================

The main reason for this release is an incompatablity bump in xdis which handles
3.7 SipHash better.

* Go over "yield" as an expression precidence
* Some small alignment with code in decompyle3 for "or" and "and" was done


3.6.5: 2020-4-1 April Fool
==========================

Back port some of the changes in decompile3 here which mostly helps 3.7 and 3.8 decompilation, although this may also help 3.6ish versions too.

- Handle nested `async for in for...`  and better async comprehension detection via `xdis`.  Still more work is needed.
- include token number in listings when `-g` and there is a parser error
- remove unneeded `Makefile`s now that remake 4.3+1.5dbg is a thing that has `-c`
- Bug in finding annotations in functions with docstrings
- Fix bug found by 2.4 sre_parse.py testing
- Fix `transform` module's  `ifelseif` bugs
- Fix bug in 3.0 name module detection
- Fix docstring detection

3.6.4: 2020-2-9 Plateau
=======================

The main focus in this release was fix some of the more glaring problems creapt in from the last release due to that refactor.

`uncompyle6` code is at a plateau where what is most needed is a code refactoring. In doing this, until everything refactored and replaced, decomplation may get worse.
Therefore, this release largely serves as a checkpoint before more major upheaval.

The upheaval, in  started last release, I believe the pinnicle was around c90ff51 which wasn't a release. I suppose I should tag that.

After c90ff5, I started down the road of redoing control flow in a more comprehensible, debuggable, and scalable way. See [The Control Flow Mess](https://github.com/rocky/python-uncompyle6/wiki/The-Control-Flow-Mess)

The bulk of the refactoring going on in the [decompyle3](https://github.com/rocky/python-decompil3) project, but I try to trickle down the changes.

It is tricky because the changes are large and I have to figure decompose things so that little testable pieces can be done. And there is also the problem that what is in decompyle3 is incomplete as well.

Other than control flow, another change that will probably happen in the next release is to redo the grammar for lambda expressions. Right now, we treat them as Python statements, you know, things with compound statements in them. But lambda aren't that. And so there is hackery to paper over difference making a statement out of an expression the wrong thing to do. For example, a return of an "and" expression can be expressed as nested "if" statements with return inside them, but the "if" variant of the bytecode is not valid in a lambda.

In the decompyle3 code, I've gone down the road making the grammar goal symbol be an expression. This also offers the opportunity to split the grammar making parsing inside lambda not only more reliable because the wrong choices don't exist, but also simpler and faster because all those rules just need don't need to exist in parsing.

I cringe in thinking about how the code has lived for so long without noticing such a simple stupidity, and lapse of sufficient thought.

Some stats from testing. The below give numbers of decompiled tests from Python's test suite which succesfully ran

```
   Version  test-suites passing
   -------  -------------------
   2.4.6     243
   2.5.6     265
   2.6.9     305
   3.3.7     300
   3.4.10    304
   3.5.9     260
   3.6.10    236
   3.7.6     306
   3.8.1     114
```

Decompiled bytecode files distributed with Python (syntax check only):

```
2.7.17  647 files:   0 failed
3.2.6   900 files:   0 failed
3.3.7  1256 files:   0 failed
3.4.10  800 files:   0 failed
3.5.9   900 files:   0 failed
3.6.10 1300 files:  28 failed
```


3.6.3: 2020-1-26 Martin and Susanne
===================================

Of late, every release fixes major gaps and embarrassments of the last release....

And in some cases, like this one, exposes lacuna and rot.

I now have [control] flow under control, even if it isn't the most optimal way.

I now have greatly expanded automated testing.

On the most recent Python versions I regularly decompile thousands of Python programs that are distributed with Python.  when it is possible, I then decompile Python's standard test suite distributed with Python and run the decompiled source code which basically checks itself. This amounts to about 250 test programs per version. This is in addition to the 3 CI testing services which do different things.

Does this mean the decompiler works perfectly? No. There are still a dozen or so failing programs, although the actual number of bugs is probably smaller though.

However, in perparation of a more major refactoring of the parser grammar, this release was born.

In many cases, decompilation is better. But there are some cases where decompilation has gotten worse. For lack of time (and interest) 3.0 bytecode suffered a hit. Possibly some code in the 3.x range did too. In time and with cleaner refactored code, this will come back.

Commit c90ff51 was a local maxiumum before, I started reworking the grammar to separate productions that were specific to loops versus those that are not in loops.
In the middle of that I added another grammar simplication to remove singleton productions of the form `sstmts-> stmts`. These were always was a bit ugly, and complicated output.

At any rate if decompilation fails, you can try c90ff51. Or another decompiler. `unpyc37` is pretty good for 3.7. wibiti `uncompyle2` is great for 2.7. `pycdc` is mediocre for Python before 3.5 or so, and not that good for the most recent Python. Geerally these programs will give some sort of answer even if it isn't correct.

decompyle3 isn't that good for 3.7 and worse for 3.8, but right now it does things no other Python decompiler like `unpyc37` or `pycdc` does. For example, `decompyle3` handles variable annotations. As always, the issue trackers for the various programs will give you a sense for what needs to be done. For now, I've given up on reporting issues in the other decompilers because there are already enough issues reported, and they are just not getting fixed anyway.


3.6.2: 2020-1-5 Samish
======================

Yet again the focus has been on just fixing bugs, mostly geared in the
later 3.x range. To get some sense what sill needs fixing, consult
test/stdlib/runtests.sh. And that only has a portion of what's known.

`make_function.py` has gotten so complex that it was split out into 3 parts
to handle different version ranges: Python <3, Python 3.0..3.6 and Python 3.7+.

An important fix is that we had been dropping docstrings in Python 3 code as a result
of a incomplete merge from the decompile3 base with respect to the transform phase.

Also important (at least to me) is that we can now handle 3.6+
variable type annotations.  Some of the decompile3 code uses that in
its source code, and I now use variable annotations in conjunction
with mypy in some of my other Python projects

Code generation for imports, especially where the import is dotted
changed a bit in 3.7; with this release are just now tracking that
change better. For this I've added pseudo instruction
`IMPORT_NAME_ATTR`, derived from the `IMPORT_NAME` instruction, to
indicate when an import contains a dotted import. Similarly, code for
3.7 `import .. as ` is basically the same as `from .. import`, the
only difference is the target of the name changes to an "alias" in the
former. As a result, the disambiguation is now done on the semantic
action side, rathero than in parsing grammar rules.

Some small specific fixes:

* 3.7+ some chained compare parsing has been fixed. Other remain.
* better if/else rule checking in the 3.4 and below range.
* 3.4+ keyword-only parameter handling was fixed more generally
* 3.3 .. 3.5 keyword-only parameter args in lambda was fixed


3.6.1: 2019-12-10 Christmas Hannukah
====================================

Overall, as in the past, the focus has been on just fixing bugs, more geared
in the later 3.x range. Handling "async for/with" in 3.8+ works better.

Numerous bugs around handling `lambda` with keyword-only and `*` args in the
3.0-3.8 have been fixed. However many still remain.

`binary_expr` and `unary_expr` have been renamed to `bin_op` and
`unary_op` to better correspond the Python AST names.

Some work was done Python 3.7+ to handle `and` better; less was done
along the lines of handling `or`. Much more is needed to improve
parsing stability of 3.7+. More of what was done with `and` needs to
be done with `or` and this will happen first in the "decompyle3"
project.

Later this will probably be extended backwards to handle the 3.6-
versions better. This however comes with a big decompilation speed
penalty. When we redo control flow this should go back to normal, but
for now, accuracy is more important than speed.

Another `assert` transform rule was added. Parser rules to distingish
`try/finally` in 3.8 were added and we are more stringent about what
can be turned into an `assert`. There was some grammar cleanup here
too.

A number of small bugs were fixed, and some administrative changes to
make `make check-short` really be short, but check more throughly what
it checks. minimum xdis version needed was bumped to include in the
newer 3.6-3.9 releases. See the `ChangeLog` for details.


3.6.0: 2019-12-10 gecko gecko
=============================

The main focus in this release was more accurate decompilation especially
for 3.7 and 3.8. However there are some improvments to Python 2.x as well,
including one of the long-standing problems of detecting the difference between
`try ... ` and `try else ...`.

With this release we now rebase Python 3.7 on off of a 3.7 base; This
is also as it is (now) in decompyle3.  This facilitates removing some of the
cruft in control-flow detection in the 2.7 uncompyle2 base.

Alas, decompilation speed for 3.7 on is greatly increased. Hopefull
this is temporary (cough, cough) until we can do a static control flow
pass.

Finally, runing in 3.9-dev is tolerated. We can disassemble, but no parse tables yet.


3.5.1 2019-11-17 JNC
====================

- Pypy 3.3, 3.5, 3.6, and 3.6.9 support
- bump xdis version to handle newer Python releases, e.g. 2.7.17, 3.5.8, and 3.5.9
- Improve 3.0 decompilation
    - no parse errors on stlib bytecode. However accurate translation in
	  control-flow and and/or detection needs work
- Remove extraneous iter() in "for" of list comprehension  Fixes #272
- "for" block without a `POP_BLOCK `and confusing `JUMP_BACK` for `CONTINUE`. Fixes #293
- Fix unmarshal incompletness detected in Pypy 3.6
- Miscellaneous bugs fixed

3.5.0 2019-10-12 Stony Brook Ride
=================================

- Fix fragment bugs
   * missing `RETURN_LAST` introduced when adding transformation layer
   * more parent entries on tokens
- Preliminary support for decompiling Python 1.0, 1.1, 1.2, and 1.6
   * Newer _xdis_ version needed

3.4.1 2019-10-02
================

- Correct assert{,2} transforms Fixes #289
- Fragment parsing fixes:
     * Wasn't handling 3-arg `%p`
   	 * fielding error in `code_deparse()`
- Use newer _xdis_ to better track Python 3.8.0


3.4.0 2019-08-24 Totoro
=======================

The main change is to add a tree-transformation phase. This simplifies the
code a little and allows us to turn `if ...: raise AssertionError` into
`assert`, and many `if ..: else if ...` into `if ... elif ..`

Use options `--show=before` and `--show=after` to see the before the tree transformation phase and after the tree transformation phase.

Most of the heavy lifting for this was done by x0ret.

Other changes:

- Fix issue #275, #283 (process to fix this bug is documented on wiki), #284
- blacken more code
- CircleCI adjustments for a changing CircleCi
- Require more recent `xdis` for Python 3.8
- Fix bugs in code using `BUILD_LIST_UNPACK` and variants

3.3.5 2019-07-03 Pre Independence Day
=====================================

Again, most of the work in this is release is thanks to x0ret.

- Handle annotation arguments in Python 3.x
- Fix _vararg_ and function signatures in 3.x
- Some 3.x < 3.6 `while` (1)/`if` fixes &mdash; others remain
- Start reinstating `else if` -> `elif`
- `LOAD_CONST` -> `LOAD_CODE` where appropriate
- option `--weak-verify` is now `--syntax-verify`
- code cleanups, start using [black](https://github.com/python/black) to reformat text


3.3.4 2019-06-19 Fleetwood at 65
================================

Most of the work in this is release is thanks to x0ret.

- Major work was done by x0ret to correct function signatures and include annotation types
- Handle Python 3.6 `STORE_ANNOTATION` [#58](https://github.com/rocky/python-uncompyle6/issues/58)
- Friendlier assembly output
- `LOAD_CONST` replaced by `LOAD_STR` where appropriate to simplify parsing and improve clarity
- remove unneeded parenthesis in a generator expression when it is the single argument to the function [#247](https://github.com/rocky/python-uncompyle6/issues/246)
- Bug in noting an async function [#246](https://github.com/rocky/python-uncompyle6/issues/246)
- Handle Unicode docstrings and fix docstring bugs [#241](https://github.com/rocky/python-uncompyle6/issues/241)
- Add short option -T as an alternate for --tree+
- Some grammar cleanup

3.3.3 2019-05-19 Henry and Lewis
================================

As before, decomplation bugs fixed. The focus has primarily been on
Python 3.7. But with this release, releases will be put on hold,as a
better control-flow detection is worked on . This has been needed for a
while, and is long overdue. It will probably also take a while to get
done as good as what we have now.

However this work will be done in a new project
[decompyle3](https://github.com/rocky/python-decompile3).  In contrast
to _uncompyle6_ the code will be written assuming a modern Python 3,
e.g. 3.7. It is originally intended to decompile Python version 3.7
and greater.

* A number of Python 3.7+ chained comparisons were fixed
* Revise Python 3.6ish format string handling
* Go over operator precedence, e.g. for AST `IfExp`

Reported Bug Fixes
------------------

* [#239: 3.7 handling of 4-level attribute import](https://github.com/rocky/python-uncompyle6/issues/239),
* [#229: Inconsistent if block in python3.6](https://github.com/rocky/python-uncompyle6/issues/229),
* [#227: Args not appearing in decompiled src when kwargs is specified explicitly (call_ex_kw)](https://github.com/rocky/python-uncompyle6/issues/227)
2.7 confusion around "and" versus comprehension "if"
* [#225: 2.7 confusion around "and" vs comprehension "if"](https://github.com/rocky/python-uncompyle6/issues/225)

3.3.2 2019-05-03 Better Friday
==============================

As before, lots of decomplation bugs fixed. The focus has primarily
been on Python 3.6. We can now parse the entire 3.6.8 Python library
and verify that without an error. The same is true for 3.5.8. A number
of the bugs fixed though are not contained to these versions. In fact
some span back as far as 2.x

But as before, many more remain in the 3.7 and 3.8 range which will
get addressed in future releases

Pypy 3.6 support was started. Pypy 3.x detection fixed (via `xdis`)

3.3.1 2019-04-19 Good Friday
==========================

Lots of decomplation bugs, especially in the 3.x series fixed. Don't worry though, many more remain.

* Add annotation return values in 3.6+
* Fix 3.6+ lambda parameter handling decompilation
* Fix 3.7+ chained comparison decompilation
* split out semantic-action customization into more separate files
* Add 3.8 try/else
* Fix 2.7 generator decompilation
* Fix some parser failures fixes in 3.4+ using test_pyenvlib
* Add more run tests

3.3.0 2019-04-14 Holy Week
==========================

* First cut at Python 3.8 (many bug remain)
* The usual smattering of bug and doc fixes

3.2.6 2019-03-23 Mueller Report
=======================================

Mostly more of the same: bug fixes and pull requests.

Bug Fixes
-----------

* [#221: Wrong grammar for nested ifelsestmt (in Python 3.7 at least)](https://github.com/rocky/python-uncompyle6/issues/221)
* [#215: 2.7 can have two JUMP_BACKs at the end of a while loop](https://github.com/rocky/python-uncompyle6/issues/215)
* [#209: Fix "if" return boundary in 3.6+](https://github.com/rocky/python-uncompyle6/issues/209),
* [#208: Comma placement in 3.6 and 3.7 **kwargs](https://github.com/rocky/python-uncompyle6/issues/208),
* [#200: Python 3 bug in not detecting end bounds of an "if" ... "elif"](https://github.com/rocky/python-uncompyle6/issues/200),
* [#155: Python 3.x bytecode confusing "try/else" with "try" in a loop](https://github.com/rocky/python-uncompyle6/issues/155),


Pull Requests
----------------

* [#202: Better "assert" statement determination in Python 2.7](https://github.com/rocky/python-uncompyle6/pull/211)
* [#204: Python 3.7 testing](https://github.com/rocky/python-uncompyle6/pull/204)
* [#205: Run more f-string tests on Python 3.7](https://github.com/rocky/python-uncompyle6/pull/205)
* [#211: support utf-8 chars in Python 3 sourcecode](https://github.com/rocky/python-uncompyle6/pull/202)



3.2.5 2018-12-30 Clear-out sale
======================================

- 3.7.2 Remove deprecation warning on regexp string that isn't raw
- main.main() parameter `codes` is not used - note that
- Improve Python 3.6+ control flow detection
- More complete fragment instruction annotation for `imports`

3.2.4 2018-10-27 7x9 release
===================================

- Bug fixes #180, #182, #187, #192
- Enhancements #189
- Internal improvements

3.2.3 2018-06-04 Michael Cohen flips and Fleetwood Redux
======================================================================
- Python 1.3 support 3.0 bug and
- fix botched parameter ordering of 3.x in last release

3.2.2 2018-06-04 When I'm 64
===================================

- Python 3.0 support and bug fixes

3.2.1 2018-06-04 MF
=======================

- Python 1.4 and 1.5 bug fixes

3.2.0 2018-05-19 Rocket Scientist
=========================================

- Add rudimentary 1.4 support (still a bit buggy)
- add --tree+ option to show formatting rule, when it is constant
- Python 2.7.15candidate1 support (via `xdis`)
- bug fixes, especially for 3.7 (but 2.7 and 3.6 and others as well)

3.1.3 2018-04-16
====================

- Add some Python 3.7 rules, such as for handling LOAD_METHOD (not complete)
- Fix some fragment bugs
- small doc changes

3.1.2 2018-04-08 Eastern Orthodox Easter
==================================================

- Python 3.x subclass and call parsing fixes
- Allow/note running on Python 3.1
- improve 3.5+ BUILD_MAP_UNPACK
- DRY instruction building code between 2.x and 3.x
- expand testing

3.1.1 2018-04-01 Easter April Fool's
=============================================

Jesus on Friday's New York Times puzzle: "I'm stuck on 2A"

- fill out 3.5+ BUILD_MAP_UNPACK (more work is needed)
- fill out 3.4+ CALL_FUNCTION_... (more work is needed)
- fill out 3.5 MAKE_FUNCTION  (more work is needed)
- reduce 3.5, 3.6 control-flow bugs
- reduce ambiguity in rules that lead to long (exponential?) parses
- limit/isolate some 2.6/2.7,3.x grammar rules
- more run-time testing of decompiled code
- more removal of parenthesis around calls via setting precedence

3.1.0 2018-03-21 Equinox
==============================

- Add code_deparse_with_offset() fragment function.
- Correct parameter call fragment deparse_code()
- Lots of 3.6, 3.x, and 2.7 bug fixes
  About 5% of 3.6 fail parsing now. But
  semantics still needs much to be desired.

3.0.1 2018-02-17
====================

- All Python 2.6.9 standard library files weakly verify
- Many 3.6 fixes. 84% of the first 200 standard library files weakly compile.
  One more big push is needed to get the remaining to compile
- Many decompilation fixes for other Python versions
- Add more to the test framework
- And more add tests target previous existing bugs more completely
- sync recent license changes in metadata

3.0.0 2018-02-17
====================

- deparse_code() and lookalikes from the various semantic actions are
  now deprecated. Instead use new API code_deparse() which makes the
  version optional and bundles debug options into a dictionary.
- License changed to GPL3.
- Many Python 3.6 fixes, especially around handling EXTENDED_ARGS
  Due to the reduction in operand size for JUMP's there are many
  more EXTENDED_ARGS instructions which can be the targets
  of jumps, and messes up the peephole-like analysis that is
  done for control flow since we don't have something better in place.
- Code has been reorganized to be more instruction nametuple based where it
  has been more bytecode array based. There was and still is code that had
  had magic numbers to advance instructions or to pick out operands.
- Bug fixes in numerous other Python versions
- Instruction display improved
- Keep global statements in fixed order (from wangym5106)

A bit more work is still needed for 3.6 especially in the area of
function calls and definitions.


2.16.0 2018-02-17
=====================

- API additions:
  - add fragments.op_at_code_loc() and
  - fragments.deparsed_find()_
- Better 2.7 end_if and COME_FROM determination
- Fix up 3.6+ CALL_FUNCTION_EX
- Misc pydisasm fixes
- Weird comprehension bug seen via new loctraceback
- Fix Python 3.5+ CALL_FUNCTION_VAR and BUILD_LIST_UNPACK in call; with this
  we can can handle 3.5+ f(a, b, *c, *d, *e) now

2.15.1 2018-02-05
=====================

- More bug fixes and revert an improper bug fix in 2.15.0

2.15.0 2018-02-05 pycon2018.co
=====================================

- Bug fixes
- Code fragment improvements
- Code cleanups
- Expand testing

2.15.1 2018-01-27
=====================

- Add `--linemap` option to give line correspondences
  between original source lines and reconstructed line sources.
  It is far from perfect, but it is a start
- Add a new class of tests: tests which when decompiled check themselves
- Split off Python version semantic action customizations into its own file
- Fix 2.7 bug in `if`/`else` loop statement
- Handle 3.6+ `EXTENDED_ARG`s for `POP_JUMP_IF..` instructions
- Correct 3.6+ calls with `kwargs`
- Describe the difficulty of 3.6 in README

2.14.3 2018-01-19
=====================

- Fix bug in 3.5+ `await` statement
- Better version to magic handling; handle 3.5.2 .. 3.5.4 versions
- Improve/correct test_pyenvlib.py status messages
- Fix some 2.7 and 2.6 parser bugs
- Fix `whilelse` parsing bugs
- Correct 2.5- decorator parsing
- grammar for decorators matches AST a little more
- better tests in setup.py for running the right version of Python
- Fix 2.6- parsing of "for .. try/else" ...  with "continue"  inside

2.14.2 2018-01-09 Samish
==============================

Decompilation bug fixes, mostly 3.6 and pre 2.7

- 3.6 `FUNCTION_EX` (somewhat)
- 3.6 `FUNCTION_EX_KW` fixes
- 3.6 `MAKE_FUNCTION` fixes
- correct 3.5 `CALL_FUNCTION_VAR`
- stronger 3.x "while 1" testing
- Fix bug in if's with "pass" bodies. Fixes #104
- try/else and try/finally fixes on 2.6-
- limit pypy customization to pypy
- Add addr fields in `COME_FROM`S
- Allow use of full instructions in parser reduction routines
- Reduce grammar in Python 3 by specialization more to specific
  Python versions
- Match Python AST names more closely when possible

2.14.1 2017-12-10 Dr. Gecko
===================================

- Many decompilation bug fixes
- Grammar rule reduction and version isolation
- Match higher-level nonterminal names more closely
  with Python AST
- Start automated Python _stdlib_ testing &mdash; full round trip

2.14.0 2017-11-26 johnnybamazing
=========================================

- Start to isolate grammar rules between versions
  and remove used grammar rules
- Fix a number of bytecode decompile problems
  (many more remain)
- Add `stdlib/runtests.sh` for even more rigorous testing

2.13.3 2017-11-13
=====================

Overall: better 3.6 decompiling and some much needed code refactoring and cleanup


- Start noting names in for template-action names; these are
  used to check/assert we have the right node type
- Simplify <import_from> rule
- Pypy 5.80-beta testing tolerance
- Start to clean up instruction mangling phase by using 3.6-style instructions
  rather trying to parse the bytecode array. This largely been done in for versions 3.x;
  3.0 custom mangling code has been reduced;
  some 2.x conversion has been done, but more is desired. This make it possible to...
- Handle `EXTENDED_ARGS` better. While relevant to all Python versions it is most noticeable in
  version 3.6+ where in switching to wordcodes the size of operands has been reduced from 2^16
  to 2^8. `JUMP` instruction then often need EXTENDED_ARGS.
- Refactor find_jump_targets() with via working of of instructions rather the bytecode array.
- use `--weak-verify` more and additional fuzzing on verify()
- fragment parser now ignores errors in nested function definitions; an parameter was
  added to assist here. Ignoring errors may be okay because the fragment parser often just needs,
  well, *fragments*.
- Distinguish `RETURN_VALUE` from `RETURN_END_IF` in exception bodies better in 3.6
- bug in 3.x language changes: import queue via `import Queue`
- reinstate some bytecode tests since decompiling has gotten better
- Revise how to report a bug

2.13.2 2017-10-12
=====================

- Re-release using a more automated approach

2.13.1 2017-10-11
=====================

- Re-release because Python 2.4 source uploaded rather than 2.6-3.6

2.13.0 2017-10-10
=====================

- Fixes in deparsing lambda expressions
- Improve table-semantics descriptions
- Document hacky customize arg count better (until we can remove it)
- Update to use `xdis` 3.7.0 or greater

2.12.0 2017-09-26
=====================

- Use `xdis` 3.6.0 or greater now
- Small semantic table cleanups
- Python 3.4's terms a little names better
- Slightly more Python 3.7, but still failing a lot
- Cross Python 2/3 compatibility with annotation arguments

2.11.5 2017-08-31
=====================

- Skeletal support for Python 3.7

2.11.4 2017-08-15
=====================

* scanner and parser now allow 3-part version string look ups,
  e.g. 2.7.1 We allow a float here, but if passed a string like '2.7'. or
* unpin 3.5.1. `xdis` 3.5.4 has been release and fixes the problems we had. Use that.
* some routines here moved to `xdis`. Use the `xdis` version
* `README.rst`: Link typo Name is _trepan2_ now not _trepan_
* xdis-forced change adjust for `COMPARE_OP` "is-not" in
  semantic routines. We need "is not".
* Some PyPy tolerance in validate testing.
* Some pyston tolerance

2.11.3 2017-08-09
=====================

Very minor changes

- RsT doc fixes and updates
- use newer `xdis`, but not too new; 3.5.2 breaks uncompyle6
- use `xdis` opcode sets
- `xdis` "exception match" is now "exception-match"

2.11.2 2017-07-09
=====================

- Start supporting Pypy 3.5 (5.7.1-beta)
- use `xdis` 3.5.0's opcode sets and require `xdis` 3.5.0
- Correct some Python 2.4-2.6 loop detection
- guard against badly formatted bytecode

2.11.1 2017-06-25
=====================

- Python 3.x annotation and function signature fixes
- Bump `xdis` version
- Small `pysource.py` bug fixes

2.11.0 2017-06-18 Fleetwood
==================================

- Major improvements in fragment tracking
  * Add nonterminal node in `extractInfo()`
  * tag more offsets in expressions
  * tag array subscripts
  * set `YIELD` value offset in a _yield expr_
  * fix a long-standing bug in not adjusting final AST when melding other deparse ASTs
- Fixes yet again for make_function node handling; document what's up here
- Fix bug in snowflake Python 3.5 `*args`, `kwargs`

2.10.1 2017-06-3 Marylin Frankel
========================================

- fix some fragments parsing bugs
  - was returning the wrong type sometimes in `deparse_code_around_offset()`
  - capture function name in offsets
  - track changes to `ifelstrmtr` node from `pysource.py` into fragments

2.10.0 2017-05-30 Elaine Gordon
=======================================

- Add fuzzy offset deparse look up
- 3.6 bug fixes
   - fix `EXTENDED_ARGS` handling (and in 2.6 and others)
   - semantic routine make_function fragments.py
   - `MAKE_FUNCTION` handling
   - `CALL_FUNCTION_EX` handling
   - `async` property on `defs`
   - support for `CALL_FUNCTION_KW` (moagstar)
- 3.5+ `UNMAP_PACK` and` BUILD_UNMAP_PACK` handling
- 3.5 FUNCTION_VAR bug
- 3.x pass statement inside `while True`
- Improve 3.2 decompilation
- Fixed `-o` argument processing (grkov90)
- Reduce scope of LOAD_ASSERT as expr to 3.4+
- `await` statement fixes
- 2.3, 2.4 "if 1 .." fixes
- 3.x annotation fixes

2.9.11 2017-04-06
=====================

- Better support for Python 3.5+ `BUILD_MAP_UNPACK`
- Start 3.6 `CALL_FUNCTION_EX` support
- Many decompilation bug fixes. (Many more remain). See ChangeLog

2.9.10 2017-02-25
=====================

- Python grammar rule fixes
- Add ability to get grammar coverage on runs
- Handle Python 3.6 opcode `BUILD_CONST_KEYMAP`

2.9.9 2016-12-16

- Remaining Python 3.5 ops handled
  (this also means more Python 3.6 ops are handled)
- Python 3.5 and 3.6 async and await handled
- Python 3.0 decompilation improved
- Python 3 annotations fixed
- Better control-flow detection
- Code cleanups and misc bug fixes

2.9.8 2016-12-16
====================

- Better control-flow detection
- pseudo instruction `THEN` in 2.x
  to disambiguate if from and
- fix bug in `--verify` option
- DRY (a little) control-flow detection
- fix syntax in tuples with one element
- if AST rule inheritance in Python 2.5
- `NAME_MODULE` removal for Python <= 2.4
- verify call fixes for Python <= 2.4
- more Python lint

2.9.7 2016-12-16
====================

- Start to handle 3.5/3.6 build_map_unpack_with_call
- Some Python 3.6 bytecode to wordcode conversion fixes
- option -g: show start-end range when possible
- track print_docstring move to help (used in python 3.1)
- verify: allow `RETURN_VALUE` to match `RETURN_END_IF`
- some 3.2 compatibility
- Better Python 3 control flow detection by adding Pseudo `ELSE` opcodes

2.9.6 2016-12-04
====================

- Shorten Python3 grammars with + and *
  this requires spark parser 1.5.1
- Add some AST reduction checks to improve
  decompile accuracy. This too requires
  spark parser 1.5.1

2.9.6 2016-11-20
====================

- Correct MANIFEST.in
- More AST grammar checking
- `--linemapping` option or _linenumbers.line_number_mapping()_
  Shows correspondence of lines between source
  and decompiled source
- Some control flow adjustments in code for 2.x.
  This is probably an improvement in 2.6 and before.
  For 2.7 things are just shuffled around a little. Sigh.
  Overall I think we are getting more precise in
  or analysis even if it is not always reflected
  in the results.
- better control flow debugging output
- Python 2 and 3 detect structure code is more similar
- Handle Docstrings with embedded triple quotes (""")

2.9.5 2016-11-13
====================

- Fix Python 3 bugs:
  * improper while 1 else
  * docstring indent
  * 3.3 default values in lambda expressions
  * start 3.0 decompilation (needs newer `xdis`)
- Start grammar misparse checking


2.9.4 2016-11-02
====================

- Handle Python 3.x function annotations
- track def keyword-parameter line-splitting in source code better
- bump min xdis version to mask previous xdis bug

2.9.3 2016-10-26
====================

Release forced by incompatibility change in` xdis` 3.2.0.

- Python 3.1 bugs:
  * handle `with`... `as`
  * handle `with`
  * Start handling `def` (...) -> _yy_ (has bugs still)

- DRY Python 3.x via inheritance
- Python 3.6 work (from Daniel Bradburn)
  * Handle 3.6 buildstring
  * Handle 3.6 handle single and multiple fstring better


2.9.2 2016-10-15
====================

- use source-code line breaks to assist in where to break
  in tuples and maps
- Fix Python 1.5 decompyle bugs
- Fix some Python 2.6 and below bugs
- DRY fragments.py code a little

2.9.1 2016-10-09
====================

- Improved Python 1.5 decompiling
- Handle old-style pre Python 2.2 classes

2.9.0 2016-10-09
====================

- Use `xdis` 3.0.0 protocol `load_module`.
  this Forces change in requirements.txt and _pkg_info_.py
- Start Python 1.5 decompiling; another round of work is needed to
  remove bugs
- Simplify python 2.1 grammar
- Fix bug with `-t` ...  Wasn't showing source text when `-t` option was given
- Fix 2.1-2.6 bug in list comprehension

2.8.4 2016-10-08
====================

- Python 3 disassembly bug fixes
- Python 3.6 fstring bug fixes (from moagstar)
- Python 2.1 disassembly
- `COME_FROM` suffixes added in Python3
- use `.py` extension in verification disassembly

2.8.3 2016-09-11 live from NYC!
=======================================

NOTE: this is possibly the last release before a major reworking of
control-flow structure detection is done.

- Lots of bug fixes in decompilation:
  * 3.0 .. 3.4 whileTrue bug
  * 3.x function declaration deparsing:
    . 3.0 .. 3.2 *args processing
    . 3.0 .. 3.2 call name and kwargs bug
    . 3.0 .. getting parameter of *
    . 3.0 .. handling variable number of args
    . 3.0 .. "if" structure bugs
  * 3.5+ if/else bugs
  * 2.2-2.6 bugs
    . try/except control flow
    . a == b == c -like detection
    . generator detection
    . "while .. and" statement bugs
    . handle "except <cond>, <var>"
    . use older raise format in 2.x
- scanner "disassemble" is now "ingest". True disassembly is done by xdis
- Start accepting Python 3.1 bytecode
- Add --weak-verify option on test_pyenvlib and test_pythonlib. This
  catches more bugs more easily
- bump xdis requirement so we can deparse dropbox 2.5 code
- Added H. Goebel's changes before 2.4 in DECOMPYLE-2.4-CHANGELOG.txt

2.8.2 2016-08-29
====================

- Handle Python 3.6 format string conversions !r, !s, !a
- Start to handle 3.1 bytecode
- Fix some PyPy translation bugs
- We now only handle 3.6.0a3+ since that is incompatible with 3.6 before that

2.8.1 2016-08-20
====================

- Add Python 2.2 decompilation

- Fix bugs
 * PyPy `LOOKUP_METHOD` bug
 * Python 3.6 `FORMAT_VALUE` handles expressions now

2.8.0 2016-08-03
====================

- Start Python 3.6 support (moagstar)
  more work on PEP 498 needed
- tidy bytecode/word output
- numerous decompiling bugs fixed
- grammar testing started
- show magic number in deparsed output
- better grammar and semantic action segregation based
  on python bytecode version

2.7.1 2016-07-26
====================

- PyPy bytecodes for 2.7 and 3.2 added
- Instruction formatting improved slightly
- 2.7 bytecode "continue" bug fixed

2.7.0 2016-07-15
====================

- Many Syntax and verification bugs removed
  tested on standard libraries from 2.3.7 to 3.5.1
  and they all decompile and verify fine.
  I'm sure there are more bugs though.

2.6.2 2016-07-11 Manhattenhenge
=======================================

- Extend bytecodes back to 2.3
- Fix bugs:
  * 3.x and 2.7 set comprehensions,
  * while1 loops
  * continue statements
- DRY and segregate grammar more

2.6.1 2016-07-08
====================

- Go over Python 2.5 bytecode deparsing
  all library programs now deparse
- Fix a couple bugs in 2.6 deparsing

2.6.0 2016-07-07
====================

- Improve Python 2.6 bytecode deparsing:
  _stdlib_ now will deparse something
- Better <2.6 vs. 2.7 grammar separation
- Fix some 2.7 deparsing bugs
- Fix bug in installing uncompyle6 script
- Doc improvements

2.5.0 2016-06-22 Summer Solstice
========================================

- Much better Python 3.2-3.5 coverage.
  3.4.6 is probably the best;3.2 and 3.5 are weaker
- Better AST printing with -t
- Better error reporting
- Better fragment offset tracking
- Some (much-needed) code refactoring

2.4.0 2016-05-18 (in memory of Lewis Bernstein)
===========================================================

- Many Python 3 bugs fixed:
  * Python 3.2 to 3.5 libraries largely
    uncompyle and most verify
- pydisassembler:
  * disassembles all code objects in a file
  * can select showing bytecode before
    or after uncompyle mangling, option -U
- DRY scanner code (but more is desired)
- Some code cleanup (but more is desired)
- Misc Bugs fixed:
  * handle complex number unmarshaling
  * Running on Python 2 to works on Python 3.5 bytecodes now

2.3.5 and 2.3.6 2016-05-14
=================================

- Python 2 class decorator fix (thanks to Tey)
- Fix fragment parsing bugs
- Fix some Python 3 parsing bugs:
  * Handling single in * parameter
  * "while True"
  * escape from for inside if
  * yield expressions
- Correct history based on info from Dan Pascu
- Fix up pip packaging, ugh.

2.3.4 2016-05-5
===================

- More Python 3.5 parsing bugs addressed
- decompiling Python 3.5 from other Python versions works
- test from Python 3.2
- remove "__module__ = __name__" in 3.0 <= Python 3.2

2.3.3 2016-05-3
===================

- Fix bug in running uncompyle6 script on Python 3
- Speed up performance on deparsing long lists by grouping in chunks of 32 and 256 items
- DRY Python expressions between Python 2 and 3

2.3.2 2016-05-1
===================

- Add `--version` option standalone scripts
- Correct License information in package
- expose functions `uncompyle_file()`, `load_file()`, and `load_module()`
- Start to DRY Python2 and Python3 grammars Separate out 3.2, and 3.5+
  specific grammar code
- Fix bug in 3.5+ constant map parsing

2.3.0, 2.3.1 2016-04-30
=============================

- Require `spark_parser` >= 1.1.0

2.2.0 2016-04-30
====================

- Spark is no longer here but pulled separate package [spark_parser](https://pypi.org/project/spark_parser/)
- Python 3 parsing fixes
- More tests

2.2.0 2016-04-02
====================

- Support single-mode (in addition to exec-mode) compilation
- Start to DRY Python 2 and Python 3 grammars
- Fix bug in if else ternary  construct
- Fix bug in uncomplye6 `-d` and `-r` options (via lelicopter)


2.1.3 2016-01-02
====================

- Limited support for decompiling Python 3.5
- Improve Python 3 class deparsing
- Handle `MAKE_CLOSURE` opcode
- Start to DRY opcode code.
- increase test coverage
- fix misc small bugs and some improvements

2.1.2 2015-12-31
====================

- Fix cross-version Marshal loading
- Handle Python 3.3 . dotted class names
- Limited 3.5 support: allows deparsing other versions
- Refactor code more, misc bug fixes

2.1.1 2015-12-27
====================

- packaging issues

2.1.0 2015-12-27
====================

- Python 3.x deparsing much more solid
- Better cross-version deparsing

Some bugs squashed while other run rampant. Some code cleanup while
much more is yet needed. More tests added, but many more are needed.


2.0.0 2015-12-11
====================

Changes from uncompyle2

- Can give code fragments given an instruction offset. See
  https://github.com/rocky/python-uncompyle6/wiki/Deparsing-technology-and-its-use-in-exact-location-reporting
- Runs under Python3. Decompiles Python 2.5-2.7 and some Python 3.2-3.4
- Allows for multiple Python grammars, specifically Python2 vs Python 3
- Add a cross-version Python disassembler command-line utility
- Add some py.test and start reorganizing tests

SPARK:
  add option to show grammar rules applied
  allow Python-style `#` comments in grammar
  Runs on Python 3 and Python 2
