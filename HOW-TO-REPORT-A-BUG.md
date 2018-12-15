<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [The difficulty of the problem](#the-difficulty-of-the-problem)
- [Is it really a bug?](#is-it-really-a-bug)
    - [Do you have valid bytecode?](#do-you-have-valid-bytecode)
    - [Semantic equivalence vs. exact source code](#semantic-equivalence-vs-exact-source-code)
- [What to send (minimum requirements)](#what-to-send-minimum-requirements)
- [What to send (additional helpful information)](#what-to-send-additional-helpful-information)
    - [But I don't *have* the source code!](#but-i-dont-have-the-source-code)
    - [But I don't *have* the source code and am incapable of figuring how how to do a hand disassembly!](#but-i-dont-have-the-source-code-and-am-incapable-of-figuring-how-how-to-do-a-hand-disassembly)
- [Narrowing the problem](#narrowing-the-problem)
- [Karma](#karma)
- [Confidentiality of Bug Reports](#confidentiality-of-bug-reports)
- [Ethics](#ethics)

<!-- markdown-toc end -->
# The difficulty of the problem

This decompiler is a constant work in progress: Python keeps
changing, and so does its code generation.

There is no Python decompiler yet that I know about that will
decompile everything. Overall, I think this one probably does the best
job of *any* Python decompiler that handles such a wide range of
versions.

But at any given time, there are a number of valid Python bytecode
files that I know of that will cause problems. See, for example, the
list in
[`test/stdlib/runtests.sh`](https://github.com/rocky/python-uncompyle6/blob/master/test/stdlib/runtests.sh).

But I understand: you would the bugs _you_ encounter addressed before
all the other known bugs.

From my standpoint, the good thing about the bugs listed in
`runtests.sh` is that each test case is small and isolated to a single
kind of problem. And I'll tend to fix easier, more isolated cases than
generic "something's wrong" kinds of bugs where I'd have to do a bit
of work to figure out what's up, if not use some sort of mind reading,
make some guesses, and perform some experiments to see if the guesses
are correct. I can't read minds, nor am I into guessing games; I'd
rather devote the effort spent instead towards fixing bugs that are
precisely defined.

And it often turns out that by just fixing the well-defined and
prescribed cases, the ill-defined amorphous cases as well will get
handled as well.

In sum, you may need to do some work to have the bug you have found
handled before the hundreds of other bugs, and other things I could be
doing.

No one is getting paid to work to work on this project, let alone the
bugs you may have an interest in. If you require decompiling bytecode
immediately, consider using a decompilation service, listed further
down in this document.

# Is it really a bug?


## Do you have valid bytecode?

As mentioned in README.rst, this project doesn't handle obfuscated
code. See README.rst for suggestions for how to remove some kinds of
obfuscation.

Checking if bytecode is valid is pretty simple: disassemble the code.
Python comes with a disassembly module called `dis`. A prerequisite
module for this package, `xdis` has a cross-python version
disassembler called `pydisasm`.

## Semantic equivalence vs. exact source code

Consider how Python compiles something like "(x*y) + 5". Early on
Python creates an "abstract syntax tree" (AST) for this. And this is
"abstract" in the sense that unimportant, redundant or unnecessary
items have been removed. Here, this means that any notion that you
wrote "x+y" in parenthesis is lost, since in this context they are
unneeded. Also lost is the fact that the multiplication didn't have
spaces around it while the addition did. It should not come as a
surprise then that the bytecode which is derived from the AST also has
no notion of such possible variation. Generally this kind of thing
isn't noticed since the Python community has laid out a very rigid set
of formatting guidelines; and it has largely beaten the community into
compliance.

Almost all versions of Python can perform some sort of code
improvement that can't be undone. In earlier versions of Python it is
rare; in later Python versions, it is more common.

If the code emitted is semantically equivalent, then this isn't a bug.


For example the code might be

```python
if a:
  if b:
     x = 1
```

and we might produce:

```python
if a and b:
  x = 1
```

These are equivalent. Sometimes

```
else:
   if ...

```

may come out as `elif` or vice versa.


As mentioned in the README, It is possible that Python changes what
you write to be more efficient. For example, for:


```python
if True:
  x = 5
```

Python will generate code like:

```python
x = 5
```

Even more extreme, if your code is:

```python
if False:
   x = 1
   y = 2
   # ...
```

Python will eliminate the entire "if" statement.

So just because the text isn't the same, does not
necessarily mean there's a bug.

# What to send (minimum requirements)

The basic requirement is pretty simple:

* Python bytecode
* Python source text

Please don't put files on download services that one has to register
for or can't get to by issuing a simple `curl` or `wget`. If you can't
attach it to the issue, or create a github gist, then the code you are
sending is too large.

Also try to narrow the bug. See below.

# What to send (additional helpful information)

Some kind folks also give the invocation they used and the output
which usually includes an error message produced. This is
helpful. From this, I can figure out what OS you are running this on
and what version of *uncomplye6* was used. Therefore, if you _don't_
provide the input command and the output from that, please give:

* _uncompyle6_ version used
* OS that you used this on
* Python interpreter version used


## But I don't *have* the source code!

Sure, I get it. No problem. There is Python assembly code on parse
errors, so simply by hand decompile that. To get a full disassembly,
use `pydisasm` from the [xdis](https://pypi.python.org/pypi/xdis)
package. Opcodes are described in the documentation for
the [dis](https://docs.python.org/3.6/library/dis.html) module.

### But I don't *have* the source code and am incapable of figuring how to do a hand disassembly!

Well, you could learn. No one is born into this world knowing how to
disassemble Python bytecode. And as Richard Feynman once said, "What
one fool can learn, so can another."

If this is too difficult, or too time consuming, or not of interest to
you, then perhaps what require is a decompilation service. [Crazy
Compilers](http://www.crazy-compilers.com/decompyle/) offers a
byte-code decompiler service for versions of Python up to 2.6. (If
there are others around let me know and I'll list them here.)

# Narrowing the problem

I don't need or want the entire source code base for the file(s) or
module(s) can't be decompiled. I just need those file(s) or module(s).
If there are problems in several files, file a bug report for each
file.

Python modules can get quite large, and usually decompilation problems
occur in a single function or maybe the main-line code but not any of
the functions or classes. So please chop down the source code by
removing those parts that do to decompile properly.

By doing this, you'll probably have a better sense of what exactly is
the problem. Perhaps you can find the boundary of what decompiles, and
what doesn't. That is useful. Or maybe the same file will decompile
properly on a neighboring version of Python. That is helpful too.

In sum, the more you can isolate or narrow the problem, the more
likely the problem will be fixed and fixed sooner.

# Karma

I realize that following the instructions given herein puts a bit of
burden on the bug reporter. In my opinion, this is justified as
attempts to balance somewhat the burden and effort needed to fix the
bug and the attempts to balance number of would-be bug reporters with
the number of bug fixers. Better bug reporters are more likely to move
in the category of bug fixers.

The barrier to reporting a big is pretty small: all you really need is
a github account, and the ability to type something after clicking
some buttons. So the reality is that many people just don't bother to
read these instructions, let alone follow it to any simulacrum.

And the reality is also that bugs sometimes get fixed even though
these instructions are not followed.

So one factors I may take into consideration is the bug reporter's karma.

* Have you demonstrably contributed to open source? I may look at your
  github profile to see what contributions you have made, how popular
  those contributions are, or how popular you are.
* How appreciative are you? Have you starred this project that you are
  seeking help from? Have you starred _any_ github project? And the above
  two kind of feed into ...
* Attitude. Some people feel that they are doing me and the world a
  great favor by just pointing out that there is a problem whose solution
  would greatly benefit them. Perhaps this is why they feel that
  instructions are not to be followed by them, nor any need for
  showing evidence gratitude when help is offered them.

# Confidentiality of Bug Reports

When you report a bug, you are giving up confidentiality to the source
code and the byte code. However, I would imagine that if you have
narrowed the problem sufficiently, confidentiality of the little that
remains would not be an issue.

However feel free to remove any comments, and modify variable names
or constants in the source code.

# Ethics

I do not condone using this program for unethical or illegal purposes.
More detestable, at least to me, is asking for help to assist you in
something that might not legitimate.

Don't use the issue tracker for such solicitations. To try to stave
off illegitimate behavior, you should note that the issue tracker, the
code, and bugs mentioned in that are in the open: there is no
confidentiality. You may be asked about the authorship or claimed
ownership of the bytecode. If I think something is not quite right, I
may label the issue questionable which may make the it easier those
who are looking for illegal activity.
