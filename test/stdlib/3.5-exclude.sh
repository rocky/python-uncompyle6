SKIP_TESTS=(
    [test_buffer.py]=1  # FIXME: Works on c90ff51
    [test_platform.py]=1  # FIXME: Works on c90ff51
    [test_pyclbr.py]=1  # FIXME: Works on c90ff51

    [test___all__.py]=1 # it fails on its own
    [test_aifc.py]=1  #
    [test_asdl_parser.py]=1 # it fails on its own
    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines

    [test_bisect.py]=1  # it fails on its own
    [test_cmath]=1
    [test_cmd_line.py]=1 #
    [test_codecmaps_cn.py]=1 # it fails on its own
    [test_codecmaps_hk.py]=1 # it fails on its own
    [test_codecmaps_jp.py]=1 # it fails on its own
    [test_codecmaps_kr.py]=1 # it fails on its own
    [test_codecmaps_tw.py]=1 # it fails on its own
    [test_codecs.py]=1 # test assertion failure
    [test_collections.py]=1
    [test_compile.py]=1  # Code introspects on co_consts in a non-decompilable way
    [test_concurrent_futures.py]=1 # Takes long to run
    [test_curses.py]=1 #

    [test_devpoll.py]=1 # it fails on its own
    [test_dict.py]=1   #
    [test_dis.py]=1   # We change line numbers - duh!
    [test_distutils.py]=1 # it fails on its own
    [test_dbm_ndbm.py]=1 # it fails on its own
    [test_descr.py]=1   # test assertion errors
    [test_doctest2.py]=1  #
    [test_doctest.py]=1  #

    [file_eintr.py]=1
    [test_enum.py]=1  #
    [test_exceptions.py]=1 # parse error

    [test_format.py]=1
    [test_ftplib.py]=1 # Test assertion failures

    [test_gdb.py]=1 # it fails on its own
    [test_glob.py]=1 #
    [test_grammar.py]=1 # parse error
    [test_grp.py]=1  # Long test

    [test_heapq.py]=1 # test assertion failures

    [test_imaplib.py]=1
    [test_inspect.py]=1 # Syntax error Investigate
    [test_io.py]=1 # Long run time.

    [test_logging.py]=1 #
    [test_long.py]=1 # too long run time: 20 seconds

    [test_marshal.py]=1 # test assertion errors
    [test_math.py]=1 # test assertion errors TypeError: a float is required
    [test_modulefinder.py]=1  # test assertion error
    [test_msilib.py]=1 # it fails on its own
    [test_multiprocessing_fork.py]=1  # long
    [test_multiprocessing_forkserver.py]=1  # long
    [test_multiprocessing_spawn.py]=1 # long

    [test_nntplib.py]=1 # too long 25 seconds
    [test_normalization.py]=1 # it fails on its own

    [test_pdb.py]=1 # probably relies on comments in code
    [test_peepholer.py]=1 # parse error; Investigate
    [test_pep352.py]=1 # test assertion error
    [test_pep380.py]=1 # Investigate test assertion differ
    [test_pickle.py]=1 # test assert errors
    [test_pkgimport.py]=1 # long
    [test_pkgutil.py]=1 # it fails on its own
    [test_print.py]=1 # test assert errors
    [test_pty.py]=1  # FIXME: Needs grammar loop isolation separation
    [test_pydoc.py]=1 # test assertion: help text difference

    [test_queue.py]=1 # Possibly parameter differences - investigate

    [test_raise.py]=1 # Test assert error
    [test_regrtest.py]=1 # test assertion errors
    [test_robotparser.py]=1 # fails on its own
    [test_runpy.py]=1 # decompile takes too long?

    [test_sched.py]=1
    [test_scope.py]=1
    [test_select.py]=1 # Takes too long 11 seconds
    [test_selectors.py]=1 # Takes too long 17 seconds
    [test_set.py]=1 # # test assert failure and doesn't terminate
    [test_signal.py]=1 # too long?
    [test_smtplib.py]=1 # probably control flow
    [test_socket.py]=1 # long
    [test_socketserver.py]=1
    [test_strtod.py]=1 # Test assert failure
    [test_subprocess.py]=1
    [test_sys_setprofile.py]=1 # test assert fail
    [test_sys_settrace.py]=1 # test assert fail

    [test_tcl.py]=1  # it fails on its own
    [test_tempfile.py]=1  # test assertion failures
    [test_thread.py]=1
    [test_threading.py]=1
    [test_timeout.py]=1
    [test_trace.py]=1 # it fails on its own
    [test_traceback.py]=1
    [test_ttk_guionly.py]=1 # it fails on its own
    [test_ttk_textonly.py]=1 # it fails on its own
    [test_typing.py]=1 # investigate syntax error

    [test_urllib.py]=1 # it fails on its own
    [test_urllib2.py]=1 # it fails on its own
    [test_urllib2_localnet.py]=1  # doesn't terminate
    [test_urllib2net.py]=1 # it fails on its own
    [test_urllibnet.py]=1 # it fails on its own
    [test_urlparse.py]=1 # test assert error
    [test_uu.py]=1 # test assert error

    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own

    [test_xmlrpc.py]=1

    [test_zipfile64.py]=1
    [test_zipimport.py]=1
    [test_zipimport_support.py]=1
    [test_zipfile.py]=1 # it fails on its own
    [test_zlib.py]=1
)
# About 260 unit-test in about 16 minutes

if (( BATCH )) ; then
    SKIP_TESTS[test_asyncore.py]=1 # Ok, but takes more than 15 seconds to run
    SKIP_TESTS[test_bisect.py]=1
    SKIP_TESTS[test_compileall.py]=1  # Something weird on POWER
    SKIP_TESTS[test_codeccallbacks.py]=1 # Something differenet in locale?
    SKIP_TESTS[test_distutils.py]=1

    SKIP_TESTS[test_exception_variations.py]=1
    SKIP_TESTS[test_ioctl.py]=1 # it fails on its own
    SKIP_TESTS[test_poplib.py]=1 # May be a result of POWER installation

    SKIP_TESTS[test_sysconfig.py]=1 # POWER extension fails
    SKIP_TESTS[test_tarfile.py]=1 # too long to run on POWER 15 secs
    SKIP_TESTS[test_venv.py]=1 # takes too long 11 seconds
fi
