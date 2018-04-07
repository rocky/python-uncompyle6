# Extracted from Python 3.5 test_abc.py
# Bug is class having only a single kwarg
# subclass.
import abc
import unittest
from inspect import isabstract

def test_abstractmethod_integration(self):
    for abstractthing in [abc.abstractmethod]:
        class C(metaclass=abc.ABCMeta):
            @abstractthing
            def foo(self): pass  # abstract
            def bar(self): pass  # concrete
        assert C.__abstractmethods__, {"foo"}
        assert isabstract(C)
        pass

test_abstractmethod_integration(None)
