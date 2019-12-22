# From 3.4 tracemalloc.py
from functools import total_ordering

@total_ordering
class Frame:
    pass


# From 3.7 test/test_c_locale_coercion.py
# Bug is multiple decorators

@test
@unittest
class LocaleCoercionTests():
    # Test implicit reconfiguration of the environment during CLI startup
    pass
