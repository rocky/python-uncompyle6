import re
import unittest
from uncompyle6.parser import get_python_parser, python_parser
from xdis.version_info import PYTHON_VERSION_TRIPLE, IS_PYPY

class TestGrammar(unittest.TestCase):
    def test_grammar(self):

        def check_tokens(tokens, opcode_set):
            remain_tokens = set(tokens) - opcode_set
            remain_tokens = set([re.sub('_\d+$','', t) for t in remain_tokens])
            remain_tokens = set([re.sub('_CONT$','', t) for t in remain_tokens])
            remain_tokens = set(remain_tokens) - opcode_set
            self.assertEqual(remain_tokens, set([]),
                    "Remaining tokens %s\n====\n%s" % (remain_tokens, p.dump_grammar()))

        p = get_python_parser(PYTHON_VERSION_TRIPLE, is_pypy=IS_PYPY)
        (lhs, rhs, tokens,
         right_recursive, dup_rhs) = p.check_sets()
        expect_lhs = set(['pos_arg', 'get_iter', 'attribute'])
        unused_rhs = set(['list', 'call', 'mkfunc',
                          'mklambda',
                          'unpack',])

        expect_right_recursive = frozenset([('designList',
                                             ('store', 'DUP_TOP', 'designList'))])
        expect_lhs.add('kwarg')

        self.assertEqual(expect_lhs, set(lhs))
        self.assertEqual(unused_rhs, set(rhs))
        self.assertEqual(expect_right_recursive, right_recursive)

        expect_dup_rhs = frozenset([('COME_FROM',), ('CONTINUE',), ('JUMP_ABSOLUTE',),
                                    ('LOAD_CONST',),
                                    ('JUMP_BACK',), ('JUMP_FORWARD',)])

        reduced_dup_rhs = {}
        for k in dup_rhs:
            if k not in expect_dup_rhs:
                reduced_dup_rhs[k] = dup_rhs[k]
                pass
            pass
        for k in reduced_dup_rhs:
            print(k, reduced_dup_rhs[k])
        # assert not reduced_dup_rhs, reduced_dup_rhs

    # FIXME: Something got borked here
    def no_test_dup_rule(self):
        import inspect
        python_parser(PYTHON_VERSION_TRIPLE, inspect.currentframe().f_code,
                      is_pypy=IS_PYPY,
                      parser_debug={
                          'dups': True, 'transition': False, 'reduce': False,
                          'rules': False, 'errorstack': None, 'context': True})
if __name__ == '__main__':
    unittest.main()
