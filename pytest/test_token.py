from uncompyle6.scanners.tok import Token

def test_token():
    # Test token formatting of: LOAD_CONST None
    t = Token('LOAD_CONST', offset=0, attr=None, pattr=None, has_arg=True)
    expect = '           0  LOAD_CONST               None'
    # print(t.format())
    assert t
    assert t.format() == expect

    # Make sure equality testing of tokens ignores offset
    t2 = Token('LOAD_CONST', offset=2, attr=None, pattr=None, has_arg=True)
    assert t2 == t


    # Make sure formatting of: LOAD_CONST False. We assume False is the 0th index
    # of co_consts.
    t = Token('LOAD_CONST', offset=1, attr=False, pattr=False, has_arg=True)
    expect = '           1  LOAD_CONST            0  False'
    assert t.format() == expect

if __name__ == '__main__':
    test_token()
