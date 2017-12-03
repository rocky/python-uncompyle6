# uncompyle2 bug was not escaping """ properly
r'''func placeholder - with ("""\nstring\n""")'''
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
