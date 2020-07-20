# From 2.7 test_descr.py
# Testing __doc__ descriptor...
# The bug in decompilation was erroneously matching
# __doc__ = as a docstring

"""This program is self-checking!"""

def test_doc_descriptor():
    # Testing __doc__ descriptor...
    # Python SF bug 542984
    class DocDescr(object):
        def __get__(self, object, otype):
            if object:
                object = object.__class__.__name__ + ' instance'
            if otype:
                otype = otype.__name__
            return 'object=%s; type=%s' % (object, otype)
    class OldClass:
        __doc__ = DocDescr()
    class NewClass(object):
        __doc__ = DocDescr()
    assert OldClass.__doc__ == 'object=None; type=OldClass'
    assert OldClass().__doc__ == 'object=OldClass instance; type=OldClass'
    assert NewClass.__doc__ == 'object=None; type=NewClass'
    assert NewClass().__doc__ == 'object=NewClass instance; type=NewClass'

test_doc_descriptor()
