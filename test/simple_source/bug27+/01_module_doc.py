# From 2.7.17 test_bdb.py
# The problem was detecting a docstring at the begining of the module
# It must be detected and change'd or else the "from __future__" below
# is invalid.
# Note that this has to be compiled with optimation < 2 or else optimization
# will remove the docstring
"""Rational, infinite-precision, real numbers."""

from __future__ import division
