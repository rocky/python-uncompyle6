# -*- coding: utf-8 -*-
# uncompyle2 bug was not escaping """ properly

# RUNNABLE!
r'''func placeholder - with ("""\nstring\n""")'''

def uni(word):
  u"""        <----- SEE 'u' HERE
  >>> mylen(u"áéíóú")
  5
  """


def foo():
    r'''func placeholder - ' and with ("""\nstring\n""")'''

def bar():
    r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """

def baz():
    """
        ...     '''>>> assert 1 == 1
        ...     '''
        ... \"""
        >>> exec test_data in m1.__dict__
        >>> exec test_data in m2.__dict__
        >>> m1.__dict__.update({"f2": m2._f, "g2": m2.g, "h2": m2.H})

        Tests that objects outside m1 are excluded:
        \"""
        >>> t.rundict(m1.__dict__, 'rundict_test_pvt')  # None are skipped.
        TestResults(failed=0, attempted=8)
    """
    assert __doc__ == r'''func placeholder - with ("""\nstring\n""")'''
    assert foo.__doc__ == r'''func placeholder - ' and with ("""\nstring\n""")'''
    assert bar.__doc__ == r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """
    assert baz.__doc__ == \
    """
        ...     '''>>> assert 1 == 1
        ...     '''
        ... \"""
        >>> exec test_data in m1.__dict__
        >>> exec test_data in m2.__dict__
        >>> m1.__dict__.update({"f2": m2._f, "g2": m2.g, "h2": m2.H})

        Tests that objects outside m1 are excluded:
        \"""
        >>> t.rundict(m1.__dict__, 'rundict_test_pvt')  # None are skipped.
        TestResults(failed=0, attempted=8)
    """
    assert uni.__doc__ ==   u"""        <----- SEE 'u' HERE
  >>> mylen(u"áéíóú")
  5
  """

baz()
