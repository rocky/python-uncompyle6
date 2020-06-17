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

    # Fails on decompyle3 as well.
    # complicated control flow and "and/or" expressions
    [test_pickle.py]=1

    [test_builtin.py]=1 # FIXME works on decompyle6
    [test_context.py]=1 # FIXME works on decompyle6
    [test_doctest2.py]=1 # FIXME works on decompyle6
    [test_format.py]=1 # FIXME works on decompyle6
    [test_marshal.py]=1 # FIXME works on decompyle6
    [test_normalization.py]=1 # FIXME works on decompyle6
    [test_os.py]=1 # FIXME works on decompyle6
    [test_pow.py]=1 # FIXME works on decompyle6
    [test_slice.py]=1 # FIXME works on decompyle6
    [test_sort.py]=1 # FIXME works on decompyle6
    [test_statistics.py]=1 # FIXME works on decompyle6
    [test_timeit.py]=1 # FIXME works on decompyle6
    [test_urllib2_localnet.py]=1 # FIXME works on decompyle6
    [test_urllib2.py]=1 # FIXME: works on uncompyle6
    [test_generators.py]=1  # FIXME: works on uncompyle6 - lambda parsing probably
    [test_grammar.py]=1 # FIXME: works on uncompyle6 - lambda parsing probably

    [test___all__.py]=1 # it fails on its own
    [test_argparse.py]=1 #- it fails on its own
    [test_asdl_parser.py]=1 # it fails on its own
    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
    [test_baseexception.py]=1  # UnboundLocalError: local variable 'exc' referenced before assignment
    [test_bdb.py]=1  #
    [test_buffer.py]=1  # parse error
    [test_clinic.py]=1 # it fails on its own
    [test_cmath.py]=1 # test assertion failure
    [test_cmd_line.py]=1  # Interactive?
    [test_cmd_line_script.py]=1
    [test_compileall.py]=1 # fails on its own
    [test_compile.py]=1  # Code introspects on co_consts in a non-decompilable way
    [test_concurrent_futures.py]=1 # too long
    [test_coroutines.py]=1 # parse error
    [test_codecs.py]=1 # test assert failures; encoding/decoding stuff
    [test_ctypes.py]=1 # it fails on its own
    [test_curses.py]=1 # probably byte string not handled properly
    [test_dataclasses.py]=1   # FIXME: control flow probably: AssertionError: unknown result 'exception'
    [test_datetime.py]=1   # Takes too long
    [test_dbm_ndbm.py]=1 # it fails on its own
    [test_decimal.py]=1   # parse error
    [test_descr.py]=1   # test assertion failures
    [test_devpoll.py]=1 # it fails on its own
    [test_dis.py]=1   # Investigate async out of place. Then We change line numbers - duh!
    [test_doctest.py]=1   # test failures
    [test_docxmlrpc.py]=1

    [test_enum.py]=1   # probably bad control flow

    [test_faulthandler.py]=1   # test takes too long before decompiling
    [test_fileinput.py]=1 # Test assertion failures
    [test_finalization.py]=1 # if/else logic
    [test_frame.py]=1 # test assertion errors
    [test_ftplib.py]=1 # parse error
    [test_fstring.py]=1 # need to disambiguate leading fstrings from docstrings
    [test_functools.py]=1 # parse error

    [test_gdb.py]=1 # it fails on its own
    [test_glob.py]=1  # TypeError: join() argument must be str or bytes, not 'tuple'
    [test_grp.py]=1 # Doesn't terminate (killed)

    [test_imaplib.py]=1  # test run loops before decompiling? More than 15 seconds to run
    [test_io.py]=1 # test takes too long to run: 37 seconds
    [test_imaplib.py]=1 # decompiled test loops - killing after 15 seconds
    [test_inspect.py]=1 # Investigate test failures involving lambda

    [test_kqueue.py]=1 # it fails on its own

    [test_lib2to3.py]=1 # it fails on its own
    [test_long.py]=1 # FIX: if boundaries wrong in Rat __init__
    [test_logging.py]=1 # test takes too long to run: 20 seconds

    [test_mailbox.py]=1 # probably control flow
    [test_math.py]=1  # test assert failures
    [test_msilib.py]=1 # it fails on its own
    [test_multiprocessing_fork.py]=1 # test takes too long to run: 62 seconds
    [test_multiprocessing_forkserver.py]=1
    [test_multiprocessing_spawn.py]=1

    [test_nntplib.py]=1 # Too long in running before decomplation takes 25 seconds

    [test_optparse.py]=1 # doesn't terminate at test_consume_separator_stop_at_option
    [test_ossaudiodev.py]=1 # it fails on its own

    [test_pdb.py]=1 # Probably relies on comments
    [test_peepholer.py]=1 # test assert error
    [test_pkg.py]=1 # Investigate: lists differ
    [test_pkgutil.py]=1 # Investigate:
    [test_poll.py]=1 # Takes too long to run before decompiling 11 seconds
    [test_pwd.py]=1 # killing - doesn't terminate
    [test_pydoc.py]=1 # it fails on its own

    [test_regrtest.py]=1 # lists differ
    [test_richcmp.py]=1 # parse error
    [test_runpy.py]=1  # Too long to run before decompiling

    [test_select.py]=1 # test takes too long to run: 11 seconds
    [test_selectors.py]=1 # Takes too long to run before decompling: 17 seconds
    [test_shutil.py]=1 # fails on its own
    [test_signal.py]=1 # Takes too long to run before decompiling: 22 seconds
    [test_smtplib.py]=1 # test failures
    [test_socket.py]=1 # Takes too long to run before decompiling
    [test_ssl.py]=1 # Takes too long to run more than 15 seconds. Probably control flow; unintialized variable
    [test_startfile.py]=1 # it fails on its own
    [test_strptime.py]=1 # parfse error
    [test_strtod.py]=1 # test assertions failed
    [test_struct.py]=1 # probably control flow
    [test_subprocess.py]=1 # Takes too long to run before decompile: 25 seconds
    [test_sys_settrace.py]=1 # parse error

    [test_tarfile.py]=1 # test assertions failed
    [test_threading.py]=1 # test assertion failers
    [test_tk.py]=1  # test takes too long to run: 13 seconds
    [test_tokenize.py]=1 # test takes too long to run before decompilation: 43 seconds
    [test_trace.py]=1  # it fails on its own
    [test_traceback.py]=1 # Probably uses comment for testing
    [test_tracemalloc.py]=1 # test assert failres
    [test_ttk_guionly.py]=1  # implementation specfic and test takes too long to run: 19 seconds
    [test_ttk_guionly.py]=1  # implementation specfic and test takes too long to run: 19 seconds
    [test_typing.py]=1 # parse error
    [test_types.py]=1 # parse error

    [test_unicode.py]=1 # unicode thing
    [test_urllibnet.py]=1 # probably control flow - uninitialized variable

    [test_weakref.py]=1 # probably control flow - uninitialized variable
    [test_with.py]=1 # probably control flow - uninitialized variable

    [test_winconsoleio.py]=1 # it fails on its own
    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own

    [test_zipfile.py]=1 # it fails on its own
    [test_zipfile64.py]=1 # Too long to run
)
# 306 unit-test files in about 19 minutes

if (( BATCH )) ; then
    SKIP_TESTS[test_capi.py]=1 # more than 15 secs to run on POWER
    SKIP_TESTS[test_dbm_gnu.py]=1 # fails on its own on POWER
    SKIP_TESTS[test_distutils.py]=1
    SKIP_TESTS[test_fileio.py]=1
    SKIP_TESTS[test_gc.py]=1
    SKIP_TESTS[test_idle.py]=1 # Probably installation specific
    SKIP_TESTS[test_sqlite.py]=1 # fails on its own on POWER
    SKIP_TESTS[test_tix.py]=1 # it fails on its own
    SKIP_TESTS[test_ttk_textonly.py]=1 # Installation dependent?
    SKIP_TESTS[test_venv.py]=1 # Too long to run: 11 seconds
    SKIP_TESTS[test_zipimport_support.py]=1

fi
