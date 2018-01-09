import sys
from uncompyle6 import PYTHON3
from uncompyle6.scanner import get_scanner
from uncompyle6.semantics.consts import (
    escape, NONE,
    # RETURN_NONE, PASS, RETURN_LOCALS
)

if PYTHON3:
    from io import StringIO
    def iteritems(d):
        return d.items()
else:
    from StringIO import StringIO
    def iteritems(d):
        return d.iteritems()

from uncompyle6.semantics.pysource import SourceWalker as SourceWalker

def test_template_engine():
    s = StringIO()
    sys_version = float(sys.version[0:3])
    scanner = get_scanner(sys_version, is_pypy=False)
    scanner.insts = []
    sw = SourceWalker(2.7, s, scanner)
    sw.ast = NONE
    sw.template_engine(('--%c--', 0), NONE)
    print(sw.f.getvalue())
    assert sw.f.getvalue() == '--None--'
    # FIXME: and so on...

from uncompyle6.semantics.consts import (
    TABLE_DIRECT, TABLE_R,
    )

from uncompyle6.semantics.fragments import (
    TABLE_DIRECT_FRAGMENT,
    )

skip_for_now = "DELETE_DEREF".split()

def test_tables():
    for t, name, fragment in (
            (TABLE_DIRECT, 'TABLE_DIRECT', False),
            (TABLE_R, 'TABLE_R', False),
            (TABLE_DIRECT_FRAGMENT, 'TABLE_DIRECT_FRAGMENT', True)):
        for k, entry in iteritems(t):
            if k in skip_for_now:
                continue
            fmt = entry[0]
            arg = 1
            i = 0
            m = escape.search(fmt)
            print("%s[%s]" % (name, k))
            while m:
                i = m.end()
                typ = m.group('type') or '{'
                if typ in frozenset(['%', '+', '-', '|', ',', '{']):
                    # No args
                    pass
                elif typ in frozenset(['c', 'p', 'P', 'C', 'D']):
                    # One arg - should be int or tuple of int
                    if typ == 'c':
                        item = entry[arg]
                        if isinstance(item, tuple):
                            assert isinstance(item[1], str), (
                            "%s[%s][%d] kind %s is '%s' should be str but is %s. "
                            "Full entry: %s" %
                            (name, k, arg, typ, item[1], type(item[1]), entry)
                            )
                            item = item[0]
                        assert isinstance(item, int), (
                            "%s[%s][%d] kind %s is '%s' should be an int but is %s. "
                            "Full entry: %s" %
                            (name, k, arg, typ, item, type(item), entry)
                            )
                    elif typ in frozenset(['C', 'D']):
                        tup = entry[arg]
                        assert isinstance(tup, tuple), (
                            "%s[%s][%d] type %s is %s should be an tuple but is %s. "
                            "Full entry: %s" %
                            (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                            )
                        assert len(tup) == 3
                        for j, x in enumerate(tup[:-1]):
                            assert isinstance(x, int), (
                                "%s[%s][%d][%d] type %s is %s should be an tuple but is %s. "
                                "Full entry: %s" %
                                (name, k, arg, j, typ, x, type(x), entry)
                                )
                        assert isinstance(tup[-1], str) or tup[-1] is None, (
                                "%s[%s][%d][%d] sep type %s is %s should be an string but is %s. "
                                "Full entry: %s" %
                                (name, k, arg, j, typ, tup[-1], type(x), entry)
                                )

                    elif typ == 'P':
                        tup = entry[arg]
                        assert isinstance(tup, tuple), (
                            "%s[%s][%d] type %s is %s should be an tuple but is %s. "
                            "Full entry: %s" %
                            (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                            )
                        assert len(tup) == 4
                        for j, x in enumerate(tup[:-2]):
                            assert isinstance(x, int), (
                                "%s[%s][%d][%d] type %s is '%s' should be an tuple but is %s. "
                                "Full entry: %s" %
                                (name, k, arg, j, typ, x, type(x), entry)
                                )
                        assert isinstance(tup[-2], str), (
                                "%s[%s][%d][%d] sep type %s is '%s' should be an string but is %s. "
                                "Full entry: %s" %
                                (name, k, arg, j, typ, x, type(x), entry)
                                )
                        assert isinstance(tup[1], int), (
                                "%s[%s][%d][%d] prec type %s is '%s' should be an int but is %s. "
                                "Full entry: %s" %
                                (name, k, arg, j, typ, x, type(x), entry)
                                )

                    else:
                        # Should be a tuple which contains only ints
                        tup = entry[arg]
                        assert isinstance(tup, tuple), (
                            "%s[%s][%d] type %s is '%s' should be an tuple but is %s. "
                            "Full entry: %s" %
                            (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                            )
                        assert len(tup) == 2
                        for j, x in enumerate(tup):
                            assert isinstance(x, int), (
                                "%s[%s][%d][%d] type '%s' is '%s should be an int but is %s. Full entry: %s" %
                                (name, k, arg, j, typ, x, type(x), entry)
                                )
                        pass
                    arg += 1
                elif typ in frozenset(['r']) and fragment:
                    pass
                elif typ == 'b' and fragment:
                    assert isinstance(entry[arg], int), (
                        "%s[%s][%d] type %s is '%s' should be an int but is %s. "
                        "Full entry: %s" %
                        (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                        )
                    arg += 1
                elif typ == 'x' and fragment:
                    tup = entry[arg]
                    assert isinstance(tup, tuple), (
                        "%s[%s][%d] type %s is '%s' should be an tuple but is %s. "
                        "Full entry: %s" %
                        (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                            )
                    assert len(tup) == 2
                    assert isinstance(tup[0], int), (
                        "%s[%s][%d] source type %s is '%s' should be an int but is %s. "
                        "Full entry: %s" %
                        (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                            )
                    assert isinstance(tup[1], tuple), (
                        "%s[%s][%d] dest type %s is '%s' should be an tuple but is %s. "
                        "Full entry: %s" %
                        (name, k, arg, typ, entry[arg], type(entry[arg]), entry)
                            )
                    for j, x in enumerate(tup[1]):
                        assert isinstance(x, int), (
                            "%s[%s][%d][%d] type %s is %s should be an int but is %s. Full entry: %s" %
                            (name, k, arg, j, typ, x, type(x), entry)
                            )
                    arg += 1
                    pass
                else:
                    assert False, (
                        "%s[%s][%d] type %s is not known. Full entry: %s" %
                            (name, k, arg, typ, entry)
                        )
                m = escape.search(fmt, i)
                pass
            assert arg == len(entry), (
                "%s[%s] arg %d should be length of entry %d. Full entry: %s" %
                            (name, k, arg, len(entry), entry))
