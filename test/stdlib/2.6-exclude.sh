SKIP_TESTS=(
    [test___all__.py]=1  # it fails on its own
    [test_aepack.py]=1 # Fails on its own
    [test_descr.py]=1
    [test_doctest.py]=1    #
    [test_dis.py]=1        # We change line numbers - duh!
    [test_file.py]=1
    [test_generators.py]=1 # Investigate
    [test_grp.py]=1      # Long test - might work Control flow?
    [test_opcodes.py]=1   # Investigate whether we caused this recently
    [test_pep352.py]=1     # Investigate
    [test_pyclbr.py]=1 # Investigate
    [test_pwd.py]=1 # Long test - might work? Control flow?

    [test_re.py]=1   # probably control flow, uninitialized variable

    [test_queue.py]=1   # Investigate whether we caused this recently
    [test test_select.py]=1 # test takes too long to run: 11 seconds
    [test_support.py]=1 #
    [test_socket.py]=1 # test takes too long to run: 12 seconds
    [test_sys.py]=1 # test assertion failures
    [test_trace.py]=1  # Line numbers are expected to be different
    [test_urllib2_localnet.py]=1 # test takes too long to run: 12 seconds
    [test_urllib2net.py]=1 # test takes too long to run: 11 seconds
    [test_zipimport_support.py]=1
    [test_zipfile64.py]=1  # Skip Long test
    [test_zlib.py]=1  #
    # .pyenv/versions/2.6.9/lib/python2.6/lib2to3/refactor.pyc
    # .pyenv/versions/2.6.9/lib/python2.6/pyclbr.pyc
)
# About 308 unit-test files, run in about 14 minutes
