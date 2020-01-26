SKIP_TESTS=(
    [test_decorators.py]=1 # FIXME: Works on c90ff51
    [test_optparse.py]=1 # FIXME: Works on c90ff51
    [test_os.py]=1 # FIXME: Works on c90ff51
    [test_pyclbr.py]=1 # FIXME: Works on c90ff51
    [test_strftime.py]=1 # FIXME: Works on c90ff51

    [test_cmd_line.py]=1
    [test_collections.py]=1
    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
    [test_datetimetester.py]=1
    [test_decimal.py]=1
    [test_dis.py]=1   # We change line numbers - duh!
    [test_quopri.py]=1 # TypeError: Can't convert 'bytes' object to str implicitly
)
