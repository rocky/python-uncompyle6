#!/usr/bin/env python
# See https://github.com/rocky/python-uncompyle6/pull/15

# In Python 2.7, you should see
#   mkfuncdeco0 ::= mkfunc
#   classdefdeco2 ::= LOAD_CONST expr mkfunc CALL_FUNCTION_0 BUILD_CLASS
#   classdefdeco1 ::= expr classdefdeco1 CALL_FUNCTION_1
#   store        ::= STORE_NAME
#   classdefdeco ::= classdefdeco1 store

def author(*author_names):
    def author_func(cls):
        return cls
    return author_func

@author('Me', 'Him')
@author('You')
class MyClass(object):
    def __init__(self):
        pass

    @staticmethod
    @staticmethod
    def static_method():
        pass

x = MyClass()
