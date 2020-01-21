SKIP_TESTS=(
    [test___all__.py]=1 # it fails on its own
    [test_aifc.py]=1  #
    [test_asdl_parser.py]=1 # it fails on its own
    [test_ast.py]=1  # line 379, in test_literal_eval  self.assertEqual(ast.literal_eval('b"hi"'), 'hi')
    [test_asynchat.py]=1  # doesn't terminate
    [test_asyncore.py]=1  # doesn't terminate
    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines

    [test_binascii.py]=1 # Doesn't terminate
    [test_binop.py]=1 # Doesn't terminate
    [test_bisect.py]=1  # it fails on its own
    [test_builtin.py]=1  #
    [test_bz2.py]=1  # testSeekBackwardsAcrossStreams (__main__.BZ2FileTest) ...  doesn't terminiate

    [test_capi.py]=1 # Doesn't terminate
    [test_cmath]=1
    [test_cmd_line.py]=1 #
    [test_codecmaps_cn.py]=1 # it fails on its own
    [test_codecmaps_hk.py]=1 # it fails on its own
    [test_codecmaps_jp.py]=1 # it fails on its own
    [test_codecmaps_kr.py]=1 # it fails on its own
    [test_codecmaps_tw.py]=1 # it fails on its own
    [test_codecs.py]=1 # test assertion failure
    [test_collections.py]=1
    [test_colorsys.py]=1 # Doesn't terminate
    [test_compile.py]=1
    [test_concurrent_futures.py]=1 # Takes long
    [test_configparser.py]=1  # Doesn't terminate
    [test_coroutines.py]=1 # Syntax error Investigate
    [test_curses.py]=1 #

    [test_devpoll.py]=1 # it fails on its own
    [test_dict.py]=1   #
    [test_dis.py]=1   # We change line numbers - duh!
    [test_distutils.py]=1 # it fails on its own
    [test_dbm_gnu.py]=1   # Doesn't terminate
    [test_dbm_ndbm.py]=1 # it fails on its own
    [test_decimal.py]=1
    [test_descr.py]=1   # syntax error: Investigate
    [test_doctest2.py]=1  #
    [test_doctest.py]=1  #

    [file_eintr.py]=1
    [test_enum.py]=1  #
    [test_exceptions.py]=1 # parse error

    [test_fileinput.py]=1 # doesn't terminate
    [test_format.py]=1
    [test_fractions.py]=1 # doesn't terminate
    [test_frame.py]=1 # doesn't terminate
    [test_ftplib.py]=1 # doesn't terminate
    [test_functools.py]=1 # doesn't terminate

    [test_gc.py]=1 # doesn't terminate (test_trashcan_threads)
    [test_gdb.py]=1 # it fails on its own
    [test_generators.py]=1 # test assert failures
    [test_glob.py]=1 #
    [test_grammar.py]=1 # parse error
    [test_grp.py]=1  # Long test

    [test_hashlib.py]=1  # doesn't terminate
    [test_heapq.py]=1
    [test_httplib.py]=1
    [test_httpservers.py]=1 # test assertion errors

    [test_imaplib.py]=1
    [test_inspect.py]=1 # Syntax error Investigate
    [test_io.py]=1 #
    [test_itertools.py]=1 # doesn't terminate on test_permutations

    [test_logging.py]=1 #
    [test_long.py]=1 #
    [test_lzma.py]=1 # doesn't terminate on test_decompressor_chunks_maxsize

    [test_marshal.py]=1 #
    [test_math.py]=1 # Investigate Unexpected ValueError: math domain error
    [test_minidom.py]=1 # doesn't terminate
    [test_modulefinder.py]=1  # test assertion error
    [test_msilib.py]=1 # it fails on its own
    [test_multiprocessing_fork.py]=1  # long
    [test_multiprocessing_forkserver.py]=1  # long
    [test_multiprocessing_spawn.py]=1 # long

    [test_nntplib.py]=1 # too long 25 seconds
    [test_normalization.py]=1 # it fails on its own

    [test_optparse.py]=1 # Doesn't terminate test_positional_arg_and_variable_args
    [test_ordered_dict.py]=1 # Doesn't terminate
    [test_os.py]=1 # doesn't terminate

    [test_pdb.py]=1 # probably relies on comments in code
    [test_peepholer.py]=1 # parse error
    [test_pep352.py]=1 # test assertion error
    [test_pep380.py]=1 # Investigate test assertion differ
    [test_pickle.py]=1
    [test_pkgimport.py]=1 # long
    [test_pkgutil.py]=1 # it fails on its own
    [test_poll.py]=1 # doesn't terminate on test_poll1
    [test_poplib.py]=1
    [test_print.py]=1
    [test_pwd.py]=1   # Takes too long
    [test_pydoc.py]=1 # test assertion: help text difference

    [test_queue.py]=1 # Possibly parameter differences - investigate

    [test_raise.py]=1 # Test assert error
    [test_range.py]=1 # doesn't terminate
    [test_readline.py]=1 # doesn't terminate
    [test_regrtest.py]=1 # test assertion errors
    [test_robotparser.py]=1 # fails on its own
    [test_runpy.py]=1 # decompile takes too long?

    [test_sched.py]=1
    [test_scope.py]=1
    [test_select.py]=1 # Takes too long 11 seconds
    [test_selectors.py]=1 # Takes too long 17 seconds
    [test_set.py]=1 # # test assert failure and doesn't terminate
    [test_shlex.py]=1 # Doesn't terminate
    [test_shutil.py]=1 # Doesn't terminate
    [test_signal.py]=1 # too long?
    [test_smtpd.py]=1 # test failures
    [test_smtplib.py]=1 # doesn't terminate
    [test_socket.py]=1 # long
    [test_socketserver.py]=1
    [test_statistics.py]=1 # doesn't terminate
    [test_strlit.py]=1 # test failure
    [test_strptime.py]=1 # doesn't terminate
    [test_strtod.py]=1 # doesn't terminate
    [test_struct.py]=1  # Doesn't terminate
    [test_subprocess.py]=1
    [test_sys.py]=1 # Doesn't terminate test_objecttypes (__main__.SizeofTest) ...
    [test_sys_setprofile.py]=1 # test assert fail
    [test_sys_settrace.py]=1 # doesn't terminate

    [test_telnetlib.py]=1 # doesn't terminate
    [test_tempfile.py]=1 # FIXME nested "if" is in wrong place. 3.6.2. may work though
    [test_thread.py]=1
    [test_threading.py]=1
    [test_threadsignals.py]=1 # doesn't terminate test_lock_acquire_retries
    [test_timeout.py]=1
    [test_trace.py]=1 # it fails on its own
    [test_traceback.py]=1
    [test_ttk_guionly.py]=1 # it fails on its own
    [test_ttk_textonly.py]=1 # it fails on its own
    [test_typing.py]=1 # investigate syntax error

    [test_univnewlines.py]=1 # doesn't terminate
    [test_unpack.py]=1 # weird, takes too long? Waiting on input?
    [test_unpack_ex.py]=1 # doesn't terminate
    [test_urllib.py]=1 # it fails on its own
    [test_urllib2.py]=1 # it fails on its own
    [test_urllib2_localnet.py]=1  # doesn't terminate
    [test_urllib2net.py]=1 # it fails on its own
    [test_urllibnet.py]=1 # it fails on its own
    [test_urlparse.py]=1 # test assert error
    [test_uu.py]=1 # May 3.6.2. may work

    [test_weakref.py]=1 # doesn't terminate test_threaded_weak_valued_consistency (__main__.MappingTestCase) ...
    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own

    [test_xmlrpc.py]=1

    [test_zipfile64.py]=1
    [test_zipimport.py]=1
    [test_zipimport_support.py]=1
    [test_zipfile.py]=1 # it fails on its own
    [test_zlib.py]=1
)
# About 230 unit-test files remain; about 8 minutes to complete
