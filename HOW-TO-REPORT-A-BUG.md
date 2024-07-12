<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Ethics](#ethics)
- [The importance of your bug report](#the-importance-of-your-bug-report)
- [The difficulty of the problem and your bug](#the-difficulty-of-the-problem-and-your-bug)
- [Is it really a bug?](#is-it-really-a-bug)
    - [Do you have valid bytecode?](#do-you-have-valid-bytecode)
    - [Semantic equivalence vs. exact source code](#semantic-equivalence-vs-exact-source-code)
- [What to send (minimum requirements)](#what-to-send-minimum-requirements)
- [What to send (additional helpful information)](#what-to-send-additional-helpful-information)
    - [But I don't *have* the source code!](#but-i-dont-have-the-source-code)
        - [But I don't *have* the source code and am incapable of figuring how to do a hand disassembly!](#but-i-dont-have-the-source-code-and-am-incapable-of-figuring-how-to-do-a-hand-disassembly)
- [Narrowing the problem](#narrowing-the-problem)
- [Karma](#karma)
- [Confidentiality of Bug Reports](#confidentiality-of-bug-reports)

<!-- markdown-toc end -->

TL;DR (too long; didn't read)

* Don't do something illegal. And don't ask me to do something illegal or help you do something illegal.
* We already have an infinite supply of decompilation bugs that need fixing, and an automated mechanism for finding more. Decompilation bugs get addressed by easiness to fix and by whim. If you expect yours to be fixed ahead of those, you need to justify why. You can ask for a hand-assisted decompilation, but that is expensive and beyond what most are willing to spend. A $100 fee is needed just to look at the bytecode.
* When asking for help, you may be asked for what you've tried on your own first. There are plenty of sources of information about this code.
* Bugs get fixed, slowly. Sometimes on the order of months or years. If you are looking for *timely* help or support, that is typically known as a _paid_ service.
* Submitting a bug or issue report that is likely to get acted upon may require a bit of effort on your part to make it easy for the problem solver. If you are not willing to do that, please don't waste your or our time. Bug report may be closed with about as much thought and care as apparent in the effort to create the bug. Supporting the project however, does increase the likelihood of your issue getting noticed and acted upon.

# Ethics

Do not use this program for unethical or illegal purposes. More detestable, at least to me, is asking for help to assist you in something that might not legitimate.

Don't use the issue tracker for such unethical or illegal solicitations. To try to stave off illegitimate behavior, you should note that the issue tracker, the code, and bugs mentioned in that are in the open: there is no
confidentiality. You may be asked about the authorship or claimed ownership of the bytecode. If I think something is not quite right, I may label the issue questionable which may make the it easier those who are looking for illegal activity.


# The importance of your bug report

For many open-source projects bugs where the expectation is that bugs are rare, reporting bugs in a *thoughtful* way can be helpful. See also [How to Ask Questions the Smart Way](http://www.catb.org/~esr/faqs/smart-questions.html).

In this project though, most of the bug reports boil down to the something like: I am trying to reverse engineer some code that I am not the author/owner and that person doesn't want me to have access to. I am hitting a problem somewhere along the line which might have to do with decompilation. But it could be something else like how the bytecode was extracted, some problem in deliberately obfuscated code, or the use some kind of Python bytecode version that isn't supported by the decompiler. Gee this stuff is complicated, here's an open source project, so maybe someone there will help me figure stuff out.

While you are free to report bugs, unless you sponsor the project, I may close them with about the same amount of effort spent that I think was used to open the report for them. And if you spent a considerable amount of time to create the bug report but didn't follow instructions given here and in the issue template, I am sorry in advance. Just go back, read, and follow instructions.

This project already has an infinite supply of bugs that have been narrowed to the most minimal form and where I have source code to compare against. And in the unlikely event this supply runs out, I have automated means for generating *another* infinite supply.

The task of justifying why addressing your bug is of use to the community, and why it should be prioritized over the others, is the bug reporter's responsibility.

While in the abstract, I have no problem answering questions about how to read a Python traceback or install Python software, or trying to understand what is going wrong in your particular setup, I am not a paid support person and there other things I'd rather be doing with my limited volunteer time. So save us both time, effort, and aggravation: use other avenues like StackOverflow. Again, justifying why you should receive unpaid help is the help requester's responsibility.


# The difficulty of the problem and your bug

This decompiler is a constant work in progress: Python keeps
changing, and so does its code generation.

There is no Python decompiler yet that I know about that will decompile everything. Overall, I think this one probably does the best job of *any* Python decompiler that handles such a wide range of versions.

But at any given time, there are a number of valid Python bytecode files that I know of that will cause problems. See, for example, the list in
[`test/stdlib/runtests.sh`](https://github.com/rocky/python-uncompyle6/blob/master/test/stdlib/runtests.sh).

There are far more bug reporters than there are bug fixers.

Unless you are a sponsor of this project, it may take a while, maybe a week or so, before the bug report is noticed, let alone acted upon. Things eventually get fixed, but it may take years. And if your bug hasn't been narrowed, it might happen as a result of some other bug fix.

# Is it really a bug?


## Do you have valid bytecode?

As mentioned in README.rst, this project doesn't handle obfuscated
code, release candidates, and the most recent versions of Python: version 3.9 and up. See README.rst for suggestions for how to remove some kinds of
obfuscation.

Checking if bytecode is valid is pretty simple: disassemble the code.
Python comes with a disassembly module called `dis`. A prerequisite
module for this package, `xdis` has a cross-python version
disassembler called `pydisasm`. Using that with the `-F extended` option, generally provides a more comprehensive disassembly than is provided by other disassemblers.

## Semantic equivalence vs. exact source code

Consider how Python compiles something like "(x*y) + 5". Early on Python creates an "abstract syntax tree" (AST) for this. And this is "abstract" in the sense that unimportant, redundant or unnecessary items have been removed. Here, this means that any notion that you wrote "x+y" in parenthesis is lost, since in this context they are unneeded. Also lost is the fact that the multiplication didn't have spaces around it while the addition did. It should not come as a surprise then that the bytecode which is derived from the AST also has no notion of such possible variation. Generally this kind of thing isn't noticed since the Python community has laid out a very rigid set of formatting guidelines; and it has largely beaten the community into compliance.

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

So just because the text isn't the same, this does not necessarily mean there's a bug.

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
and what version of *uncompyle6* was used. Therefore, if you _don't_
provide the input command and the output from that, please give:

* _uncompyle6_ version used
* OS that you used this on
* Python interpreter version used


## But I don't *have* the source code!

There is Python assembly code on parse errors, so simply by hand decompile that. To get a full disassembly, use `pydisasm` from the [xdis](https://pypi.python.org/pypi/xdis) package. Opcodes are described in the documentation for the [dis](https://docs.python.org/3.6/library/dis.html) module.

### But I don't *have* the source code and am incapable of figuring how to do a hand disassembly!

Well, you could learn. No one is born into this world knowing how to disassemble Python bytecode. And as Richard Feynman once said, "What one fool can learn, so can another."

If this is too difficult, or too time consuming, or not of interest to you, then you might consider [sponsoring](https://github.com/sponsors/rocky) the project. [Crazy
Compilers](http://www.crazy-compilers.com/decompyle/) offers a byte-code decompiler service for versions of Python up to 2.6. (If there are others around let me know and I'll list them here.) Don't be surprised if I ask you to pay for work (if I think the work is ethical) when you want me to work on your problem that I think isn't of interest or benefit to anyone but yourself or a small limited number of people, or I think the need is questionable.

# Narrowing the problem

I don't need or want the entire source code base for the file(s) or module(s) can't be decompiled. I just need those file(s) or module(s). If there are problems in several files, file a bug report for each file.

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
burden on the bug reporter. This is justified since it attempts to balance
the burden and effort needed to fix the bug with the amount of effort to report the problem. And it attempts
to balance number of would-be bug reporters with the number of bug
fixers. Better bug reporters are more likely to move in the category
of bug fixers.

The barrier to reporting a big is pretty small: all you really need is
a github account, and the ability to type something after clicking
some buttons. So the reality is that many people just don't bother to
read these instructions, let alone follow it to any simulacrum.

That said, bugs sometimes get fixed even though these instructions are not followed.

I may take into consideration is the bug reporter's karma.

* Have you demonstrably contributed to open source? I may look at your github profile to see what contributions you have made, how popular those contributions are, or how popular you are.
* How appreciative are you? Have you starred this project that you are seeking help from? Have you starred _any_ github project? And the above two kind of feed into ...
* Attitude. Some people feel that they are doing me and the world a
  great favor by just pointing out that there is a problem whose
  solution would greatly benefit them. (This might account partially
  for the fact that those that have this attitude often don't read or
  follow instructions such as those given here.)


# Confidentiality of Bug Reports

When you report a bug, you are giving up confidentiality to the source
code and the byte code. However, I would imagine that if you have
narrowed the problem sufficiently, confidentiality of the little that
remains would not be an issue.

However feel free to remove any comments, and modify variable names
or constants in the source code.

If there is some legitimate reason to keep confidentiality, you can contact me by email to explain the extenuating circumstances. However I tend to discard without reading anonymous email.

Private consulting available via https://calendly.com/rb3216 rates: $150 for 30 minutes; $250 for 60 minutes.
