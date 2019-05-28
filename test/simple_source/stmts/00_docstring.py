# -*- coding: utf-8 -*-
# uncompyle2 bug was not escaping """ properly

# RUNNABLE!
r'''func placeholder - with ("""\nstring\n""")'''

def dq0():
    assert __doc__ == r'''func placeholder - with ("""\nstring\n""")'''

def dq1():
    """assert that dedent() has no effect on 'text'"""
    assert dq1.__doc__ == """assert that dedent() has no effect on 'text'"""

def dq2():
    '''assert that dedent() has no effect on 'text\''''
    assert dq1.__doc__ == '''assert that dedent() has no effect on 'text\''''

def dq3():
    """assert that dedent() has no effect on 'text\""""
    assert dq3.__doc__ == """assert that dedent() has no effect on 'text\""""

def dq4():
    """assert that dedent() has no effect on 'text'"""
    assert dq4.__doc__ == """assert that dedent() has no effect on 'text'"""

def dq5():
    r'''func placeholder - ' and with ("""\nstring\n""")'''
    assert dq5.__doc__ == r'''func placeholder - ' and with ("""\nstring\n""")'''

def dq6():
    r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """
    assert dq6.__doc__ == r"""func placeholder - ' and with ('''\nstring\n''') and \"\"\"\nstring\n\"\"\" """

def dq7():
  u"""        <----- SEE 'u' HERE
  >>> mylen(u"áéíóú")
  5
  """
  assert dq7.__doc__ ==   u"""        <----- SEE 'u' HERE
  >>> mylen(u"áéíóú")
  5
  """

def dq8():
  u"""        <----- SEE 'u' HERE
  >>> mylen(u"تست")
  5
  """
  assert dq8.__doc__ ==   u"""        <----- SEE 'u' HERE
  >>> mylen(u"تست")
  5
  """

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

dq0()
dq1()
dq2()
dq3()
dq4()
dq5()
dq6()
dq7()
dq8()
baz()
