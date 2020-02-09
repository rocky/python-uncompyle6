# Python3.5 bug from abc.py:
#   stmt ::= LOAD_CLOSURE RETURN_VALUE RETURN_LAST
#
# And this gets ignored.

# Note this is similar to 06_classbug.py but not the same.
#  classmethod -> object

class abstractclassmethod(classmethod):
    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super().__init__(callable)

# From 2.7.17 test_abc.py
# Bug was handling OldstyleClass correctly without
# a "return locals() but with a "pass"
class OldstyleClass:
    pass
