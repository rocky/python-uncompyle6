SKIP_TESTS=(
    [test_cgi.py]=1 # FIXME: Works on c90ff51

    [test_bsddb3.py]=1 # test takes too long to run: 110 seconds
    [test_compile.py]=1  # Code introspects on co_consts in a non-decompilable way
    [test_curses.py]=1  # Possibly fails on its own but not detected
    [test_cmd_line.py]=1 # Takes too long, maybe hangs, or looking for interactive input?
    [test_dis.py]=1   # We change line numbers - duh!
    [test_doctest.py]=1 # Fails on its own
    [test_exceptions.py]=1
    [test_format.py]=1 # Control flow "and" vs nested "if"
    [test_grammar.py]=1     # Too many stmts. Handle large stmts
    [test_grp.py]=1     # test takes to long, works interactively though
    [test_io.py]=1 # Test takes too long to run
    [test_ioctl.py]=1 # Test takes too long to run
    [test_lib2to3.py]=1 # test takes too long to run: 28 seconds
    [test_math.py]=1
    [test_memoryio.py]=1 # FIX
    [test_modulefinder.py]=1 # FIX
    [test_multiprocessing.py]=1 # On uncompyle2, takes 24 secs
    [test_poll.py]=1  # test takes too long to run: 11 seconds
    [test_regrtest.py]=1 #
    [test_runpy.py]=1   # Long and fails on its own
    [test_select.py]=1  # Runs okay but takes 11 seconds
    [test_socket.py]=1  # Runs ok but takes 22 seconds
    [test_ssl.py]=1  #
    [test_subprocess.py]=1 # Runs ok but takes 22 seconds
    [test_sys_settrace.py]=1 # Line numbers are expected to be different

    [test_tokenize.py]=1 # test takes too long to run: 19 seconds
    [test_traceback.py]=1 # Line numbers change - duh.
    [test_unicode.py]=1  # Too long to run 11 seconds
    [test_xpickle.py]=1 # Runs ok but takes 72 seconds
    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
    [test_zipimport.py]=1  #
)
# 334 unit-test files in about 15 minutes

if (( BATCH )) ; then
    # Fails in crontab environment?
    # Figure out what's up here
    SKIP_TESTS[test_array.py]=1
    SKIP_TESTS[test_ast.py]=1
    SKIP_TESTS[test_audioop.py]=1
    SKIP_TESTS[test_doctest2.py]=1 # a POWER thing?
    SKIP_TESTS[test_httplib.py]=1  # Ok, but POWER has problems with this
    SKIP_TESTS[test_pdb.py]=1 # Ok, but POWER has problems with this
    SKIP_TESTS[test_tarfile.py]=1 # test can take over 15 seconds to run on an overloaded POWER7 system

    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
    SKIP_TESTS[test_base64.py]=1
fi
