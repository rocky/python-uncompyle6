SKIP_TESTS=(
    [test_ast.py]=1 # FIXME: Works on c90ff51
    [test_cmath.py]=1  # FIXME: Works on c90ff51
    [test_format.py]=1 # FIXME: Works on c90ff51
    [test_ftplib.py]=1 # FIXME: Works on c90ff51
    [test_slice.py]=1 # FIXME: Works on c90ff51
    [test_sort.py]=1 # FIXME: Works on c90ff51
    [test_timeit.py]=1 # FIXME: Works on c90ff51
    [test_os.py]=1 # parse error FIXME: Works on c90ff51

    [test___all__.py]=1  # it fails on its own
    [test_aifc.py]=1  #
    [test_argparse.py]=1 # it fails on its own
    [test_asdl_parser.py]=1 # it fails on its own
    [test_asyncgen.py]=1  # parse error
    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines

    [test_baseexception.py]=1 # test assert error
    [test_bdb.py]=1  #
    [test_bisect.py]=1  # it fails on its own
    [test_buffer.py]=1  # parse error
    [test_builtin.py]=1  # Fails on its own

    [test test_capi.py]=1 # it fails on its own
    [test_cmd_line.py]=1 # Interactive?
    [test_codeccallbacks.py]=1 # TypeError: ... must return (str/bytes, int) tuple
    [test_codecencodings_cn.py]=1 # it fails on its own
    [test_codecencodings_hk.py]=1 # it fails on its own
    [test_codecencodings_iso2022.py]=1 # it fails on its own
    [test_codecencodings_jp.py]=1 # it fails on its own
    [test_codecencodings_kr.py]=1 # it fails on its own
    [test_codecencodings_tw.py]=1 # it fails on its own
    [test_codecmaps_cn.py]=1 # it fails on its own
    [test_codecmaps_hk.py]=1 # it fails on its own
    [test_codecmaps_jp.py]=1 # it fails on its own
    [test_codecmaps_kr.py]=1 # it fails on its own
    [test_codecmaps_tw.py]=1 # it fails on its own
    [test_codecs.py]=1
    [test_collections.py]= # it fails on its own
    [test_compile.py]=1  # Code introspects on co_consts in a non-decompilable way
    [test_concurrent_futures.py]=1 # Takes long
    [test_contextlib.py]=1 # test assertion failure
    [test_contextlib_async.py]=1 # Investigate
    [test_coroutines.py]=1 # parse error
    [test_curses.py]=1 # Parse error
    [test_ctypes.py]=1 # it fails on its own

    [test_datetime.py]=1 # it fails on its own
    [test_dbm_ndbm.py]=1 # it fails on its own
    [test_decimal.py]=1
    [test_decorators.py]=1 # control-flow failures
    [test_descr.py]=1   # syntax error: Investigate
    [test_devpoll.py]=1 # it fails on its own
    [test_dict.py]=1 # it fails on its own
    [test_dis.py]=1   # We change line numbers - duh!
    [test_doctest2.py]=1  #
    [test_doctest.py]=1  #
    [test_docxmlrpc.py]=1 # it fails on its own
    [test_dtrace.py]=1 # it fails on its own
    [test_dummy_thread.py]=1 # it fails on its own

    [test_enum.py]=1  #
    [test_exceptions.py]=1   # parse error

    [test_filecmp.py]=1   # parse error
    [test_file_eintr.py]=1   # parse error
    [test_fileinput.py]=1 # doesn't terminate
    [test_finalization.py]=1
    [test_float.py]=1 # it fails on its own
    [test_functools.py]=1 # it fails on its own
    [test_fstring.py]=1 # need to disambiguate leading fstrings from docstrings
    [test___future__.py]=1 # syntax error: Investigate

    [test_gdb.py]=1 # it fails on its own
    [test_generators.py]=1 # FIXME: Invalid syntax: f2 = lambda : (yield from g())        if False:
    [test_genexps.py]=1 #
    [test_glob.py]=1 #
    [test_grammar.py]=1 # parse error

    [test_hashlib.py]=1 # it fails on its own
    [test_heapq.py]=1 # it fails on its own

    [test_io.py]=1 # it fails on its own
    [test_imaplib.py]=1
    [test_inspect.py]=1 # Syntax error Investigate
    [test_itertools.py]=1 # test assertion failures

    [test_kqueue.py]=1 # it fails on its own

    [test_lib2to3.py]=1 # it fails on its own
    [test_logging.py]=1 # it fails on its own
    [test_long.py]=1 #
    [test_lzma.py]=1 # fails on its own

    [test_mailbox.py]=1 # it fails on its own
    [test_marshal.py]=1 #
    [test_math.py]=1 # test assert errors call param Investigate
    [test_metaclass.py]=1
    [test_modulefinder.py]=1  # test assertion error
    [test_msilib.py]=1 # it fails on its own
    [test_multiprocessing_fork.py]=1 # it fails on its own
    [test_multiprocessing_forkserver.py]=1 # it fails on its own
    [test_multiprocessing_main_handling.py]=1 # takes too long -  11 seconds
    [test_multiprocessing_spawn.py]=1 # it fails on its own

    [test_nntplib.py]=1 # test takes too long to run: 31 seconds
    [test_normalization.py]=1 # it fails on its own

    [test_optparse.py]=1 # test fails
    [test_ordered_dict.py]=1 # it fails on its own
    [test_ossaudiodev.py]=1 # it fails on its own

    [test_pdb.py]=1 # Probably introspection
    [test_peepholer.py]=1
    [test_pickle.py]=1
    [test_pkgimport.py]=1 # it fails on its own
    [test_platform.py]=1
    [test_plistlib.py]=1
    [test_poll.py]=1 # Takes too long 11 seconds
    [test_poplib.py]=1
    [test_pprint.py]=1 # it fails on its own
    [test_pulldom.py]=1
    [test_pyclbr.py]=1 # it fails on its own
    [test_pydoc.py]=1 # it fails on its own

    [test_random.py]=1 # it fails on its own
    [test_range.py]=1
    [test_regrtest.py]=1 # test takes too long to run: 12 seconds
    [test_robotparser.py]=1
    [test_runpy.py]=1 # decompile takes too long?

    [test_sax.py]=1 # it fails on its own
    [test_sched.py]=1
    [test_scope.py]=1
    [test_secrets.py]=1 # it fails on its own
    [test_select.py]=1 # test takes too long to run: 11 seconds
    [test_selectors.py]=1 # it fails on its own
    [test_shutil.py]=1 # it fails on its own
    [test_signal.py]=1 # it fails on its own
    [test_site.py]=1 # it fails on its own
    [test_smtpd.py]=1
    [test_smtplib.py]=1 # it fails on its own
    [test_socket.py]=1 # long
    [test_socketserver.py]=1
    [test_ssl.py]=1 # it fails on its own
    [test_startfile.py]=1 # it fails on its own
    [test_statistics.py]=1 # it fails on its own
    [test_string_literals.py]=1
    [test_strftime.py]=1 # test assertion failures
    [test_strtod.py]=1 # it fails on its own
    [test_struct.py]=1  # test assertion errors
    [test_subprocess.py]=1
    [test_sys.py]=1 # Investigate confusing "and" with nested "if" when there is an "else
    [test_sys_settrace.py]=1 # parse error
    [test_sysconfig.py]=1 # if confused for ifelse in "test_triplet_in_ext_suffix"

    [test_tarfile.py]=1 # it fails on its own
    [test_tcl.py]=1 # Test assert failures
    [test_telnetlib.py]=1 # takes more than 15 seconds to run
    [test_thread.py]=1 # it fails on its own
    [test_threading.py]=1
    [test_threadsignals.py]=1

    [test_time.py]=1 # Works but not on POWER: Rounding error?

    [test_timeout.py]=1
    [test_tix.py]=1 # it fails on its own
    [test_tk.py]=1 # it fails on its own
    [test_tokenize.py]=1 # test takes too long to run: 80 seconds
    [test_trace.py]= # it fails on its own
    [test_traceback.py]=1
    [test_tracemalloc.py]=1
    [test_ttk_guionly.py]= # it fails on its own
    [test_ttk_textonly.py]=1 # it fails on its own
    [test_turtle.py]=1 # it fails on its own
    [test_typing.py]=1 # investigate syntax error

    [test_ucn.py]=1 # it fails on its own
    [test_urllib2_localnet.py]=1 # long
    [test_urllib2net.py]=1 # it fails on its own
    [test_urllib2.py]=1 # it fails on its own
    [test_urllibnet.py]=1 # it fails on its own
    [test_urllib.py]=1 # it fails on its own
    [test_urlparse.py]=1 # test failure

    [test_venv.py]=1 # test takes too long to run: 13 seconds

    [test_weakref.py]=1
    [test_winconsoleio.py]=1 # it fails on its own
    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own

    [test_xmlrpc.py]=1 # it fails on its own

    [test_zipfile.py]=1 # Too long - 11 seconds
    [test_zipfile64.py]=1
    [test_zipimport.py]=1
    [test_zipimport_support.py]=1
    [test_zlib.py]=1
)
# 236 unit-test files in about 13 minutes

if (( BATCH )) ; then
    SKIP_TESTS[test_codeccallbacks.py]=1
    SKIP_TESTS[test_complex.py]=1 # Something funky with POWER8

    # locale on test machine is probably customized
    SKIP_TESTS[test__locale.py]=1
fi
