# Python 3.3 and above only
# Tests

# 3.3, 3.4
# yield_from ::= expr expr YIELD_FROM
# expr ::= yield_from

# 3.5:
# yield_from ::= expr GET_YIELD_FROM_ITER LOAD_CONST YIELD_FROM

def _walk_dir(dir, dfile, ddir=None):
    yield from _walk_dir(dir, ddir=dfile)

# From 3.5.1 _wakrefset.py
#
#  3.5:
#  withstmt ::= expr SETUP_WITH POP_TOP suite_stmts_opt
#              POP_BLOCK LOAD_CONST COME_FROM
#              WITH_CLEANUP_START WITH_CLEANUP_FINISH END_FINALLY


def __iter__(self, IterationGuard):
    with IterationGuard(self):
        for itemref in self.data:
            item = itemref()
            if item is not None:
                yield item
