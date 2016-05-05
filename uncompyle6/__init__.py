"""
  Copyright (c) 1999 John Aycock
  Copyright (c) 2000 by hartmut Goebel <h.goebel@crazy-compilers.com>
  Copyright (c) 2015 by Rocky Bernstein

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

from __future__ import print_function

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

sys.setrecursionlimit(5000)

def check_python_version(program):
    if not (sys.version_info[0:2] in ((2, 6), (2, 7), (3, 2), (3, 3), (3, 4), (3, 5))):
        print('Error: %s requires Python 2.6, 2.7, 3.2, 3.3, 3.4 or 3.5' % program,
              file=sys.stderr)
        sys.exit(-1)
    return

import uncompyle6.semantics.pysource
import uncompyle6.semantics.fragments
import uncompyle6.load

# Export some functions
from uncompyle6.load import load_module, load_file
from uncompyle6.main import uncompyle_file

# Conventience functions so you can say:
# from uncompyle6 import deparse_code

deparse_code = uncompyle6.semantics.pysource.deparse_code
