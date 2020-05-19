SKIP_TESTS=(
    # FIXME: Did this work sometime in the past ?
    #   for elem in g(s):
    #     if not tgt and isOdd(elem): continue
    # is erroneously:
    #   for elem in g(s):
    #    if tgt or isOdd(elem):
    #       pass
    #    else:
    #       tgt.append(elem)
    [test_itertools.py]=1

    [test_buffer.py]=1  # FIXME: Works on c90ff51
    [test_cmath.py]=1  # FIXME: Works on c90ff51

    [test_atexit.py]=1  # The atexit test starting at 3.3 looks for specific comments in error lines

    [test_cmd_line.py]=1 # too long?
    [test_concurrent_futures.py]=1  # too long?

    [test_decimal.py]=1 # test takes too long to run: 18 seconds
    [test_descr.py]=1  # test assertion errors
    [test_doctest.py]=1  # test assertion errors
    [test_doctest2.py]=1  # test assertion errors
    [test_dis.py]=1   # We change line numbers - duh!

    [test_exceptions.py]=1   #
    [test_faulthandler.py]=1
    [test_fork1.py]=1 # test takes too long to run: 12 seconds

    [test_grammar.py]=1

    [test_io.py]=1  # test takes too long to run: 34 seconds

    [test_lib2to3.py]=1
    [test_logging.py]=1 # test takes too long to run: 13 seconds
    [test_long.py]=1 # test assert failure AttributeError: 'Rat' object has no attribute 'd'

    [test_math.py]=1
    [test_modulefinder.py]=1
    [test_multiprocessing.py]=1

    [test_nntplib.py]=1

    [test_pep352.py]=1  # test failures
    [test_peepholer.py]=1
    [test_poll.py]=1  # test takes too long to run: 11 seconds
    [test_pty.py]=1  # FIXME: Needs grammar loop isolation separation

    [test_queue.py]=1

    [test_re.py]=1
    [test_resource.py]=1
    [test_runpy.py]=1

    [test_scope.py]=1
    [test_select.py]=1
    [test_signal.py]=1
    [test_socket.py]=1
    [test_ssl.py]=1 # too installation specific
    [test_subprocess.py]=1  # test takes too long to run: 28 seconds
    [test_sys_setprofile.py]=1 # test assertion errors
    [test_sys_settrace.py]=1 # test assertion errors

    [test_tcl.py]=1  # installation specific; it fails on its own
    [test_timeout.py]=1 # Too long to run: 19 seconds
    [test_traceback.py]=1 # Probably introspects code

    [test_zipfile64.py]=1 # Too long to run
)
# About 300 unit-test files in about 20 minutes

if (( BATCH )) ; then
    SKIP_TESTS[test_ftplib.py]=1  # Runs too long on POWER; over 15 seconds
    SKIP_TESTS[test_idle.py]=1  # No tk
    SKIP_TESTS[test_pep352.py]=1  # UnicodeDecodeError may be funny on weird environments
    SKIP_TESTS[test_pep380.py]=1  # test_delegating_generators_claim_to_be_running ?
    # Fails in crontab environment?
    # Figure out what's up here
    # SKIP_TESTS[test_exception_variations.py]=1
fi
