# Tests:
#   importstmt ::= LOAD_CONST LOAD_CONST import_as
#   import_as ::= IMPORT_NAME store

#   Since Python 3.3:
#     classdef   ::= buildclass store
#     store      ::= STORE_NAME
#     buildclass ::= LOAD_BUILD_CLASS mkfunc LOAD_CONST expr CALL_FUNCTION_3
#     mkfunc     ::= LOAD_CONST LOAD_CONST MAKE_FUNCTION_0

import io
class BZ2File(io.BufferedIOBase):
    pass


class ABC(metaclass=BZ2File):
    pass
