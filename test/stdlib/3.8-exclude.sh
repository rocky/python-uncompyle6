SKIP_TESTS=(
    [test_mimetypes.py]=1 # parse error. decompile3 works. Release 3.6.4 works?
    [test_time.py]=1 # FIXME: parse eror. decompyle3 works. Release 3.6.4 works?
    [test_aifc.py]=1 # parse error; decompile3 works

    [test_doctest2.py]=1 # test failures release 3.6.4 works?
    [test_finalization.py]=1  # test failures release 3.6.4 works?
    [test_urllib2.py]=1 # FIXME: works on uncompyle6?
    [test_zipimport.py]=1 # FIXME: works on uncompyle6

    # From decompyle3 excludes
    # Very Simple example. Compare with 3.7 Need 3.8 parse rules for exception handling return
    #    for proto in p:
    #    try:
    #        drop = 5
    #    except StopIteration:
    #        continue

    [test_dict.py]=1 #

    # Simple example. Compare with 3.7 Need 3.8 parse rules for exception handling return
    #    try:
    #    return 5
    # except KeyError:
    #    return res
    # except TypeError:
    #    return 10

    # These and the above may be due to new code generation or tests
    # between 3.8.3 and 3.8.5 ?
    [test_decorators.py]=1 #

    [test_dtrace.py]=1 #
    [test_exceptions.py]=1 #
    [test_ftplib.py]=1 #
    [test_gc.py]=1 #
    [test_gzip.py]=1 #
    [test_hashlib.py]=1 #
    [test_iter.py]=1 #
    [test_itertools.py]=1 #

    [test___all__.py]=1 # it fails on its own
    [test_argparse.py]=1 #- it fails on its own
    [test_array.py]=1 #- parse error
    [test_asdl_parser.py]=1 # it fails on its own
    [test_ast.py]=1  # Depends on comments in code
    [test_asyncgen.py]=1 # parse error
    [test_asynchat.py]=1 # parse error
    [test_asyncore.py]=1 # parse error
    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
    [test_audioop.py]=1  # test failure
    [test_audit.py]=1  # parse error

    [test_base64.py]=1  # parse error
    [test_baseexception.py]=1  #
    [test_bigaddrspace.py]=1  # parse error
    [test_bigmem.py]=1  # parse error
    [test_bdb.py]=1  #
    [test_binascii.py]=1  # test failure
    [test_binhex.py]=1  # parse error
    [test_binop.py]=1  # parse error
    [test_bool.py]=1  # parse error
    [test_buffer.py]=1  # parse error
    [test_builtin.py]=1  # parse error
    [test_bytes.py]=1  # parse error
    [test_bz2.py]=1  # parse error

    [test_calendar.py]=1  # parse error
    [test_cgi.py]=1  # parse error
    [test_cgitb.py]=1  # parse error
    [test_clinic.py]=1 # it fails on its own
    [test_cmath.py]=1 # test assertion failure
    [test_cmd.py]=1  # parse error
    [test_cmd_line.py]=1  # Interactive?
    [test_cmd_line_script.py]=1
    [test_code_module.py]=1 # test failure
    [test_codecmaps_cn.py]=1 # test before decompile takes too long to run 135 secs
    [test_codecmaps_hk.py]=1 # test before decompile takes too long to run 46 secs
    [test_codecs.py]=1
    [test_collections.py]=1
    [test_compare.py]=1
    [test_compile.py]=1
    [test_compileall.py]=1 # fails on its own
    [test_complex.py]=1 # Investigate
    [test_concurrent_futures.py]=1 # too long
    [test_configparser.py]=1
    [test_context.py]=1
    [test_contextlib.py]=1 # parse error
    [test_contextlib_async.py]=1 # parse error
    [test_coroutines.py]=1 # Parse error
    [test_cprofile.py]=1 # parse error
    [test_crypt.py]=1 # Parse error
    [test_csv.py]=1 # Parse error
    [test_ctypes.py]=1 # it fails on its own
    [test_curses.py]=1 # Parse error

    [test_dataclasses.py]=1  # test assertion errors
    [test_datetime.py]=1   # Takes too long
    [test_dbm.py]=1   # parse error
    [test_dbm_dumb.py]=1   # parse error
    [test_dbm_gnu.py]=1   # Takes too long
    [test_dbm_ndbm.py]=1 # it fails on its own
    [test_decimal.py]=1   # Parse error
    [test_decorators.py]=1   # parse error
    [test_deque.py]=1   # parse error
    [test_descr.py]=1   # Parse error
    [test_descrtut.py]=1   # parse error
    [test_devpoll.py]=1 # it fails on its own
    [test_dict.py]=1   # parse error
    [test_dictcomps.py]=1 # Bad semantics - Investigate
    [test_difflib.py]=1   # parse error
    [test_dis.py]=1   # We change line numbers - duh!
    [test_doctest.py]=1 # parse error
    [test_doctest2.py]=1 # test faiures relesae 3.6.4 works?
    [test_docxmlrpc.py]=1
    [test_dtrace.py]=1 # parse error
    [test_dummy_thread.py]=1 # parse error

    [test_embed.py]=1   # parse error
    [test_ensureip.py]=1   #
    [test_ensurepip.py]=1 # parse error
    [test_enum.py]=1   #
    [test_enumerate.py]=1   #
    [test_eof.py]=1   # parse error
    [test_epoll.py]=1   # parse error
    [test_exception_hierarchy.py]=1 # control flow?
    [test_exceptions.py]=1   # parse error

    [test_faulthandler.py]=1   # takes too long
    [test_file_eintr.py]=1 # too long to run test; works on 3.7.7
    [test_fcntl.py]=1
    [test_filecmp.py]=1   # parse error
    [test_fileinput.py]=1
    [test_fileio.py]=1
    [test_float.py]=1  # Takes a long time to decompile
    [test_flufl.py]=1  # parse error
    [test_format.py]=1
    [test_frame.py]=1
    [test_frozen.py]=1 # parse error
    [test_fstring.py]=1 # Investigate
    [test_ftplib.py]=1
    [test_functools.py]=1
    [test_future.py]=1 # parse error
    [test___future__.py]=1 # test failure
    [test_future5.py]=1 # parse error

    [test_gc.py]=1 # parse error
    [test_gdb.py]=1 # it fails on its own
    [test_genericpath.py]=1 # parse error
    [test_generators.py]=1  # improper decompile of assert i < n and (n-i) % 3 == 0
    [test_getpass.py]=1  # parse error
    [test_gettext.py]=1  # parse error
    [test_glob.py]=1  #
    [test_grammar.py]=1
    [test_grp.py]=1 # Doesn't terminate (killed)
    [test_gzip.py]=1 # parse error

    [test_hashlib.py]=1 # test assert failures
    [test_heapq.py]=1  # test failure
    [test_hmac.py]=1  # parse error
    [test_httplib.py]=1 # parse error
    [test_http_cookiejar.py]=1
    [test_httpservers.py]=1 # parse error

    [test_imghdr.py]=1 # parse error
    [test_imp.py]=1 # parse error
    [test_int.py]=1 # parse error
    [test_io.py]=1 # test takes too long to run: 37 seconds
    [test_ioctl.py]=1 # parse error
    [test_imaplib.py]=1
    [test_ipaddress.py]=1 # parse error
    [test_index.py]=1
    [test_inspect.py]=1
    [test_iter.py]=1 # parse error
    [test_itertools.py]=1 # parse error

    [test_keywordonlyarg.py]=1 # parse error
    [test_kqueue.py]=1 # it fails on its own

    [test__locale.py]=1 # parse error
    [test_largefile.py]=1 # parse error
    [test_lib2to3.py]=1 # it fails on its own
    [test_linecache.py]=1 # parse error
    [test_lltrace.py]=1 # parse error
    [test_locale.py]=1 # parse error
    [test_logging.py]=1 # test takes too long to run: 20 seconds
    [test_long.py]=1 # investigate
    [test_lzma.py]=1 # it fails on its own

    [test_mailbox.py]=1 # parse error
    [test_mailcap.py]=1 # parse error
    [test_marshal.py]=1
    [test_math.py]=1
    [test_memoryio.py]=1 # test failure
    [test_memoryview.py]=1 # parse error
    [test_minidom.py]=1 # test failure
    [test_mmap.py]=1 # parse error
    [test_modulefinder.py]=1
    [test_msilib.py]=1
    [test_multiprocessing_fork.py]=1 # test takes too long to run: 62 seconds
    [test_multiprocessing_forkserver.py]=1
    [test_multiprocessing_main_handling.py]=1 # parse error
    [test_multiprocessing_spawn.py]=1

    [test_named_expressions.py]=1 # parse error
    [test_netrc.py]=1 # parse error
    [test_nis.py]=1 # break outside of loop
    [test_normalization.py]=1 # probably control flow (uninitialized variable)
    [test_nntplib.py]=1
    [test_ntpath.py]=1

    [test__osx_support.py]=1 # parse error
    [test_opcodes.py]=1 # parse error
    [test_operator.py]=1 # parse error
    [test_optparse.py]=1 # doesn't terminate (killed)
    [test_ordered_dict.py]=1 # parse error
    [test_os.py]=1 # probably control flow (uninitialized variable)
    [test_ossaudiodev.py]=1 # it fails on its own
    [test_osx_env.py]=1 # parse error

    [test_pathlib.py]=1 # parse error
    [test_pdb.py]=1 # Probably relies on comments
    [test_peepholer.py]=1 # decompile takes a long time; then test assert error
    [test_pickle.py]=1 # Probably relies on comments
    [test_picklebuffer.py]=1 # parse error
    [test_pipes.py]=1 # parse error
    [test_pkg.py]=1 # Investigate: lists differ
    [test_pkgimport.py]=1 # parse error
    [test_pkgutil.py]=1 # Investigate:
    [test_platform.py]=1 # parse error
    [test_plistlib.py]=1 # parse error
    [test_poll.py]=1
    [test_popen.py]=1 # parse error
    [test_poplib.py]=1 # Parse error
    [test_positional_only_arg.py]=1 # test failures
    [test_posixpath.py]=1 # parse error
    [test_posix.py]=1 # parse error
    [test_print.py]=1 # parse error
    [test_profile.py]=1 # parse error
    [test_pwd.py]=1 # killing - doesn't terminate
    [test_pulldom.py]=1 # killing - doesn't terminate
    [test_py_compile.py]=1 # parse error
    [test_pyexpat.py]=1 # parse error
    [test_pyclbr.py]=1 # test failure
    [test_pydoc.py]=1 # it fails on its own

    [test_queue.py]=1  # parse error

    [test_raise.py]=1  # parse error
    [test_random.py]=1  # parse error
    [test_range.py]=1  # parse error
    [test_rcompleter.py]=1  # parse error
    [test_re.py]=1 # test assertion error
    [test_readline.py]=1  # parse error
    [test_robotparser.py]=1  # too long to run before decompiling: 31 secs
    [test_regrtest.py]=1 # lists differ
    [test_reprlib.py]=1 # parse error
    [test_resource.py]=1  # parse error
    [test_richcmp.py]=1 # parse error
    [test_runpy.py]=1  #

    [test_sax.py]=1 # parse error
    [test_sched.py]=1 # parse error
    [test_scope.py]=1 # parse error
    [test_script_helper.py]=1 # parse error
    [test_select.py]=1 # test takes too long to run: 11 seconds
    [test_selectors.py]=1
    [test_set.py]=1 # parse error
    [test_shelve.py]=1 # parse error
    [test_shlex.py]=1 # probably control flow
    [test_shutil.py]=1 # fails on its own
    [test_signal.py]=1 #
    [test_site.py]=1 # parse error
    [test_slice.py]=1 # Investigate
    [test_smtpd.py]=1 # parse error
    [test_smtplib.py]=1 #
    [test_smtpnet.py]=1 # parse error
    [test_socket.py]=1
    [test_socketserver.py]=1
    [test_sort.py]=1 # Probably control flow; unintialized varaible
    [test_source_encoding.py]=1 # parse error
    [test_spwd.py]=1 # parse error
    [test_ssl.py]=1 # Probably control flow; unintialized varaible
    [test_startfile.py]=1 # it fails on its own
    [test_stat.py]=1 # test assertions failed
    [test_statistics.py]=1 # Probably control flow; unintialized varaible
    [test_strftime.py]=1 # parse error
    [test_string.py]=1 # parse error
    [test_string_literals.py]=1 # parse error
    [test_strptime.py]=1 # test assertions failed
    [test_strtod.py]=1 # test assertions failed
    [test_struct.py]=1 # test assertions failed
    [test_structmembers.py]=1 # test assertions failed
    [test_subclassinit.py]=1 # parse error
    [test_subprocess.py]=1
    [test_super.py]=1 # parse error
    [test_support.py]=1 # parse error
    [test_symbol.py]=1 # parse error
    [test_sys.py]=1 # parse error
    [test_sys_setprofile.py]=1 # test assertions failed
    [test_sys_settrace.py]=1 # parse error
    [test_sysconfig.py]=1 # parse error

    [test_tabnanny.py]=1 # parse error
    [test_tarfile.py]=1 # parse error
    [test_tcl.py]=1 # parse error
    [test_telnetlib.py]=1 # parse error
    [test_tempfile.py]=1 # parse error
    [test_thread.py]=1 # parse error
    [test_threaded_import.py]=1 # parse error
    [test_threading.py]=1 #
    [test_timeit.py]=1 # probably control flow uninitialized variable
    [test_timeout.py]=1 # parse error
    [test_tk.py]=1  # test takes too long to run: 13 seconds
    [test_tokenize.py]=1
    [test_trace.py]=1  # it fails on its own
    [test_traceback.py]=1 # Probably uses comment for testing
    [test_tracemalloc.py]=1 #
    [test_ttk_guionly.py]=1  # implementation specfic and test takes too long to run: 19 seconds
    [test_turtle_import.py]=1 # parse error
    [test_turtle.py]=1 # parse error
    [test_types.py]=1 # parse error
    [test_typing.py]=1 # parse error

    [test_ucn.py]=1 # parse error
    [test_unicode.py]=1 # unicode thing
    [test_unicode_file_functions.py]=1 # parse faiure
    [test_unicodedata.py]=1 # test faiure
    [test_univnewlines.py]=1 # parse error
    [test_urllib.py]=1 # parse error
    [test_urllib2.py]=1 #
    [test_urllib_response.py]=1 # parse error
    [test_urllib2_localnet.py]=1 #
    [test_urllib2net.py]=1 # parse error
    [test_urllibnet.py]=1 # probably control flow - uninitialized variable
    [test_urlparse.py]=1 # parse error
    [test_userdict.py]=1 # test failures
    [test_userstring.py]=1 # parse error
    [test_utf8.py]=1 # parse error
    [test_utf8_mode.py]=1 # parse error
    [test_uu.py]=1 # parse error
    [test_uuid.py]=1 # parse error

    [test_venv.py]=1 # parse error

    [test_weakref.py]=1 # probably control flow - uninitialized variable
    [test_weakset.py]=1 # parse error
    [test_webbrowser.py]=1 # parse error
    [test_with.py]=1 # probably control flow - uninitialized variable
    [test_winconsoleio.py]=1 # it fails on its own
    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own
    [test_wsgiref.py]=1 # parse error

    [test_xml_etree.py]=1 # parse error
    [test_xmlrpc.py]=1 # parse error
    [test__xxsubinterpreters.py]=1 # parse error

    [test_yield_from.py]=1 # parse error

    [test_zlib.py]=1 # test looping take more than 15 seconds to run
    [test_zipapp.py]=1 # parse error
    [test_zipimport_support.py]=1 # parse error
    [test_zipfile.py]=1 # it fails on its own
    [test_zipfile64.py]=1 #
)
# 114 test files, Elapsed time about 7 minutes

if (( BATCH )) ; then
    SKIP_TESTS[test_idle.py]=1 # Probably installation specific
    SKIP_TESTS[test_tix.py]=1 # fails on its own
    SKIP_TESTS[test_ttk_textonly.py]=1 # Installation dependent?

fi
