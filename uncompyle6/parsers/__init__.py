"""Here we have parser grammars for the different Python versions.
Instead of full grammars, we have full grammars for certain Python versions
and the others indicate differences between a neighboring version.

For example Python 2.6, 2.7, 3.2, and 3.7 are largely "base" versions
which work off off parse2.py, parse3.py, and parse37base.py.

Some examples:
Python 3.3 diffs off of 3.2; 3.1 and 3.0 diff off of 3.2; Python 1.0..Python 2.5 diff off of
Python 2.6 and Python 3.8 diff off of 3.7
"""
