from uncompyle6 import PYTHON3
from uncompyle6.semantics.consts import (
    NONE,
    # RETURN_NONE, PASS, RETURN_LOCALS
)

if PYTHON3:
    from io import StringIO
else:
    from StringIO import StringIO

from uncompyle6.semantics.pysource import SourceWalker as SourceWalker

def test_template_engine():
    s = StringIO()
    sw = SourceWalker(2.7, s, None)
    sw.ast = NONE
    sw.template_engine(('--%c--', 0), NONE)
    print(sw.f.getvalue())
    assert sw.f.getvalue() == '--None--'
