SKIP_TESTS=(
    [test_descr.py]=1
    # [test_descr.py]=pytest_module # FIXME: Works on c90ff51?
    # AssertionError: 'D(4)C(4)A(4)' != 'D(4)C(4)B(4)A(4)'
    # - D(4)C(4)A(4)
    # + D(4)C(4)B(4)A(4)
    # ?         ++++


    [test_cmath.py]=1 # Control-flow "elif else -> else: if else"
    # [test_cmath.py]=pytest_module
    # AssertionError: rect1000: rect(complex(0.0, 0.0))
    # Expected: complex(0.0, 0.0)
    # Received: complex(0.0, -1.0)
    # Received value insufficiently close to expected value.


    [test_cmd_line.py]=1

    [test_collections.py]=1 # fail on its own
    # E   TypeError: __new__() takes exactly 4 arguments (1 given)

    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
    [test_datetime.py]=pytest_module

    [test_decimal.py]=1 # Fails on its own, even with pytest

    [test_dictcomps.py]=1
    # [test_dictcomps.py]=pytest_module # FIXME: semantic error: actual = {k:v for k in }
    #    assert (count * 2) <= i

    [test_doctest.py]=1 # Missing pytest fixture
    # [test_doctest.py]=pytest_module
    # fixture 'coverdir' not found

    [test_dis.py]=1   # We change line numbers - duh!

    [test_exceptions.py]=1 # parse error
    # [test_exceptions.py]=pytest_module # parse error

    [test_modulefinder.py]=1 # test failures
    [test_multiprocessing.py]=1 # test takes too long to run: 35 seconds

    [test_peepholer.py]=1
    [test_pep352.py]=1

    [test_runpy.py]=1

    [test_ssl.py]=1 # too installation specific
    [test_startfile.py]=1 # fails on its own
    [test_subprocess.py]=1  # fails on its own
    [test_tcl.py]=1 # it fails on its own
    [test_tk.py]=1 # it fails on its own
    [test_traceback.py]=1 # it fails on its own
    [test_zipfile64.py]=1 # Too long to run

)

if (( BATCH )) ; then
    # Fails in crontab environment?
    # Figure out what's up here
    SKIP_TESTS[test_exception_variations.py]=1
fi
