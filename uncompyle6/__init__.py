"""
  Copyright (c) 2015, 2018 by Rocky Bernstein
  Copyright (c) 2000 by hartmut Goebel <h.goebel@crazy-compilers.com>
  Copyright (c) 1999 John Aycock

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

  NB. This is not a masterpiece of software, but became more like a hack.
  Probably a complete rewrite would be sensefull. hG/2000-12-27
"""

import sys

__docformat__ = 'restructuredtext'

PYTHON3 = (sys.version_info >= (3, 0))

# We do this crazy way to support Python 2.6 which
# doesn't support version_major, and has a bug in
# floating point so we can't divide 26 by 10 and get
# 2.6
PYTHON_VERSION = sys.version_info[0] + (sys.version_info[1] / 10.0)
PYTHON_VERSION_STR  = "%s.%s" % (sys.version_info[0], sys.version_info[1])

IS_PYPY = '__pypy__' in sys.builtin_module_names

if hasattr(sys, 'setrecursionlimit'):
    # pyston doesn't have setrecursionlimit
    sys.setrecursionlimit(5000)

import uncompyle6.semantics.pysource
import uncompyle6.semantics.fragments

# Export some functions
from uncompyle6.main import decompile_file

# For compatibility
uncompyle_file = decompile_file

# Convenience functions so you can say:
# from uncompyle6 import (code_deparse, deparse_code2str)

code_deparse = uncompyle6.semantics.pysource.code_deparse
deparse_code2str = uncompyle6.semantics.pysource.deparse_code2str

# This is deprecated:
deparse_code = uncompyle6.semantics.pysource.deparse_code
