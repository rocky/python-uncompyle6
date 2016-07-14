# Tests:
#   2.7:
#   assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1
#   call_function ::= expr expr expr CALL_FUNCTION_2

#   2.6
#   assert ::= assert_expr jmp_true LOAD_ASSERT RAISE_VARARGS_1 come_from_pop

assert isinstance(1, int)

# 2.6.9 DocXMLRPCServer.py
# 2.6
# assert2 ::= assert_expr jmp_true LOAD_ASSERT expr RAISE_VARARGS_2 come_from_pop

for method_name in ['a']:
    if method_name in ('b',):
        method = 'a'
    else:
        assert 0, "instance installed"

    methods = 'b'

# _Bug in 3.x is not recognizing the assert
# producing:
#   if not not do_setlocal:
#      raise AssertError

def getpreferredencoding(do_setlocale=True):
    assert not do_setlocale
