#!/bin/bash
me=${BASH_SOURCE[0]}

typeset -i batch=1
isatty=$(/usr/bin/tty 2>/dev/null)
if [[ -n $isatty ]] && [[ "$isatty" != 'not a tty' ]] ; then
    batch=0
fi


function displaytime {
  local T=$1
  local D=$((T/60/60/24))
  local H=$((T/60/60%24))
  local M=$((T/60%60))
  local S=$((T%60))
  (( $D > 0 )) && printf '%d days ' $D
  (( $H > 0 )) && printf '%d hours ' $H
  (( $M > 0 )) && printf '%d minutes ' $M
  (( $D > 0 || $H > 0 || $M > 0 )) && printf 'and '
  printf '%d seconds\n' $S
}

# Python version setup
FULLVERSION=$(pyenv local)
PYVERSION=${FULLVERSION%.*}
MINOR=${FULLVERSION##?.?.}

STOP_ONERROR=${STOP_ONERROR:-1}

typeset -i timeout=15

function timeout_cmd {

  (
    $@ &
    child=$!
    trap -- "" SIGTERM
    (
	sleep "$timeout"
	if ps -p $child >/dev/null ; then
	    echo ""
	    echo >&1 "**Killing ${2}; takes more than $timeout seconds to run"
	    kill -TERM ${child}
	fi
    ) &
    wait "$child"
  )
}

typeset -A SKIP_TESTS
case $PYVERSION in
    2.4)
	SKIP_TESTS=(
	    [test_decimal.py]=1  #
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_generators.py]=1  # Investigate
	    [test_grammar.py]=1    # Too many stmts. Handle large stmts
	    [test_grp.py]=1      # Long test - might work Control flow?
	    [test_pep247.py]=1 # Long test - might work? Control flow?
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_socketserver.py]=1 # -- test takes too long to run: 40 seconds
	    [test_threading.py]=1 # test takes too long to run: 11 seconds
	    [test_thread.py]=1 # test takes too long to run: 36 seconds
	    [test_trace.py]=1 # Long test - works
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.5)
	SKIP_TESTS=(
 	    [test_coercion.py]=1
 	    [test_decimal.py]=1
 	    [test_dis.py]=1        # We change line numbers - duh!
	    [test_generators.py]=1 # Investigate
	    [test_grammar.py]=1    # Too many stmts. Handle large stmts
	    [test_grp.py]=1        # Long test - might work Control flow?
	    [test_pdb.py]=1        # Line-number specific
	    [test_pep352.py]=1     # Investigate
	    [test_pwd.py]=1 # Long test - might work? Control flow?
	    [test_pyclbr.py]=1 # Investigate
	    [test_queue.py]=1 # Control flow?
	    [test_socketserver.py]=1 # Too long to run - 42 seconds
	    [test_struct.py]=1 # "if and" confused for if .. assert and
	    [test_threading.py]=1 # test takes too long to run: 11 seconds
	    [test_thread.py]=1 # test takes too long to run: 36 seconds
	    [test_trace.py]=1  # Line numbers are expected to be different
	    [test_urllib2net.py]=1 # is interactive?
	    [test_zipfile64.py]=1  # Runs ok but takes 204 seconds
	)
	;;
    2.6)
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
	    [test_queue.py]=1   # Investigate whether we caused this recently
	    [test test_select.py]=1 # test takes too long to run: 11 seconds
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
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_aifc.py]=1
	    SKIP_TESTS[test_array.py]=1

	    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
	    SKIP_TESTS[test_base64.py]=1

	    # output indicates expected == output, but this fails anyway.
	    # Maybe the underlying encoding is subtlely different so it
	    # looks the same?
	fi
	;;
    2.7)
	SKIP_TESTS=(
	    [test_bsddb3.py]=1 # test takes too long to run: 110 seconds
	    [test_compile.py]=1  # Investigate: unable to find constant 0j in (None, 0.0)
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
	    [test_pwd.py]=1     # Takes too long
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
	# About 335 unit-test remaining files run in about 20 minutes and 11 seconds
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_array.py]=1
	    SKIP_TESTS[test_ast.py]=1
	    SKIP_TESTS[test_audioop.py]=1
	    SKIP_TESTS[test_httplib.py]=1  # Ok, but POWER has problems with this
	    SKIP_TESTS[test_pdb.py]=1 # Ok, but POWER has problems with this

	    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
	    SKIP_TESTS[test_base64.py]=1
	fi
	;;
    3.0)
	SKIP_TESTS=(
	    [test_array.py]=1  # Handling of bytestring
	    [test_binascii.py]=1 # handling of bytearray?
	    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
	    [test_datetimetester.py]=1
	    [test_decimal.py]=1
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_fileio.py]=1
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;
    3.1)
	SKIP_TESTS=(
	    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_fileio.py]=1
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;
    3.2)
	SKIP_TESTS=(
	    [test_cmd_line.py]=1
	    [test_collections.py]=1
	    [test_concurrent_futures.py]=1 # too long to run over 46 seconds by itself
	    [test_datetimetester.py]=1
	    [test_decimal.py]=1
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_quopri.py]=1 # TypeError: Can't convert 'bytes' object to str implicitly
	)
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;

    3.3)
	SKIP_TESTS=(
	    [test_atexit.py]=1  # The atexit test staring at 3.3 looks for specific comments in error lines
	    [test_buffer.py]=1  # parse error
	    [test_cmd_line.py]=1 # too long?
	    [test_concurrent_futures.py]=1  # too long?
	    [test_decimal.py]=1 # test takes too long to run: 18 seconds
	    [test_descr.py]=1  # test assertion errors
	    [test_dictcomps.py]=1  # test assertion errors
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
	    [test_math.py]=1
	    [test_modulefinder.py]=1
	    [test_multiprocessing.py]=1
	    [test_nntplib.py]=1
	    [test_peepholer.py]=1
	    [test_poll.py]=1  # test takes too long to run: 11 seconds
	    [test_queue.py]=1
	    [test_raise.py]=1 # test assertion errors
	    [test_resource.py]=1
	    [test_re.py]=1
	    [test_runpy.py]=1
	    [test_scope.py]=1
	    [test_select.py]=1
	    [test_set.py]=1
	    [test_signal.py]=1
	    [test_socket.py]=1
	    [test_ssl.py]=1 # too installation specific
	    [test_strlit.py]=1
	    [test_symtable.py]=1
	    [test_sys_setprofile.py]=1 # test assertion errors
	    [test_sys_settrace.py]=1
	    [test_subprocess.py]=1  # test takes too long to run: 28 seconds
	    [test_thread.py]=1
	    [test_timeout.py]=1
	    [test_traceback.py]=1
	    [test_urllib2.py]=1
	    [test_warnings.py]=1
	    [test_zipfile.py]=1 # too long - 12 second
	    [test_zipfile64.py]=1
	    [test_zipimport.py]=1
	    [test_zipimport_support.py]=1
	)

	# About 300 unit-test files in about 20 minutes
	if (( batch )) ; then
	    SKIP_TESTS[test_idle.py]=1  # No tk
	    SKIP_TESTS[test_pep352.py]=1  # UnicodeDecodeError may be funny on weird environments
	    SKIP_TESTS[test_pep380.py]=1  # test_delegating_generators_claim_to_be_running ?
	    # Fails in crontab environment?
	    # Figure out what's up here
	    # SKIP_TESTS[test_exception_variations.py]=1
	fi
	;;

    3.4)
	SKIP_TESTS=(
	    [test___all__.py]=1  # it fails on its own
	    [test_aifc.py]=1  #
	    [test_asynchat.py]=1  #
	    [test_asyncore.py]=1  #
	    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
	    [test_bdb.py]=1  #
	    [test_binascii.py]=1 # Doesn't terminate
	    [test_binop.py]=1 # Doesn't terminate
	    [test_buffer.py]=1  # parse error
	    [test_builtin.py]=1  # Doesn't terminate
	    [test_bz2.py]=1  # Doesn't terminate
	    [test_capi.py]=1 # Doesn't terminate
	    [test_cmd_line.py]=1
	    [test_colorsys.py]=1 # Doesn't terminate
	    [test_concurrent_futures.py]=1  # too long?
	    [test_configparser.py]=1  # Doesn't terminate
	    [test_ctypes.py]=1 # it fails on its own
	    [test_curses.py]=1 # Investigate
	    [test_dbm_gnu.py]=1   # Doesn't terminate
	    [test_decimal.py]=1 # test takes too long to run: 18 seconds
	    [test_devpoll.py]=1 # it fails on its own
	    [test_descr.py]=1   # Doesn't terminate
	    [test_dictcomps.py]=1 # test assertion failure
	    [test_dict.py]=1   #
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_distutils.py]=1 # it fails on its own
	    [test_doctest2.py]=1
	    [test_doctest.py]=1
	    [test_docxmlrpc.py]=1
	    [test_enum.py]=1
	    [test_exceptions.py]=1
	    [test_faulthandler.py]=1
	    [test_file_eintr.py]=1   # parse error
	    [test_fileinput.py]=1 # doesn't terminate
	    [test_fork1.py]=1 # too long
	    [test_fractions.py]=1 # doesn't terminate
	    [test_frame.py]=1 # doesn't terminate
	    [test_ftplib.py]=1 # doesn't terminate
	    [test_functools.py]=1 # doesn't terminate
	    [test_gdb.py]=1 # it fails on its own
	    [test_gc.py]=1 # doesn't terminate
	    [test_grammar.py]=1
	    [test_generators.py]=1 # test assert failures
	    [test_grp.py]=1  # Long test
	    [test_hashlib.py]=1  # doesn't terminate
	    [test_heapq.py]=1
	    [test_httpservers.py]=1
	    [test_httplib.py]=1 # it fails on its ow
	    [test_import.py]=1 # it fails on its own
	    [test_io.py]=1
	    [test_ioctl.py]=1 # it fails on its own
	    [test_inspect.py]=1 # Syntax error Investigate
	    [test_itertools.py]=1 # doesn't terminate on test_permutations
	    [test_logging.py]=1 #
	    [test_long.py]=1 #
	    [test_marshal.py]=1 #
	    [test_math.py]=1 #
	    [test_minidom.py]=1 # Does not termiate
	    [test_mmap.py]=1
	    [test_modulefinder.py]=1  # test assertion error
	    [test_multiprocessing_fork.py]=1 # doesn't terminate
	    [test_multiprocessing_forkserver.py]=1 # doesn't terminate
	    [test_multiprocessing_main_handling.py]=1  # doesn't terminate
	    [test_multiprocessing_spawn.py]=1 # doesn't terminate
	    [test_nntplib.py]=1 # doesn't terminate#
	    [test_ordered_dict.py]=1
	    [test_os.py]=1 # Doesn't terminate
	    [test_peepholer.py]=1
	    [test_pep352.py]=1
	    [test_pep380.py]=1
	    [test_pickle.py]=1
	    [test_pkgimport.py]=1 # long
	    [test_poll.py]=1
	    [test_poplib.py]=1
	    [test_pwd.py]=1   # Takes too long
	    [test_pydoc.py]=1
	    [test_queue.py]=1
	    [test_raise.py]=1
	    [test_re.py]=1
	    [test_resource.py]=1
	    [test_runpy.py]=1
	    [test_sched.py]=1
	    [test_scope.py]=1
	    [test_select.py]=1 # Too long 11 seconds
	    [test_selectors.py]=1  # Too long; 11 seconds
	    [test_set.py]=1
	    [test_shlex.py]=1
	    [test_shutil.py]=1
	    [test_signal.py]=1
	    [test_smtplib.py]=1
	    [test_sndhdr.py]=1
	    [test_socket.py]=1 # long 25 seconds
	    [test_socketserver.py]=1 # long 25 seconds
	    [test_statistics.py]=1 # doesn't terminate
	    [test_struct.py]=1  # Doesn't terminate
	    [test_strlit.py]=1 # test failure
	    [test_strptime.py]=1 # doesn't terminate
	    [test_strtod.py]=1 # doesn't terminate
	    [test_subprocess.py]=1 # Too long
	    [test_symtable.py]=1 # Investigate bad output
	    [test_sys.py]=1 # Doesn't terminate
	    [test_sys_settrace.py]=1 # Doesn't terminate
	    [test_sys_setprofile.py]=1
	    [test_telnetlib.py]=1 # Doesn't terminate
	    [test_thread.py]=1
	    [test_threading.py]=1 # Too long
	    [test_threadsignals.py]=1
	    [test_timeout.py]=1
	    [test_traceback.py]=1 # test failure
	    [test_tracemalloc.py]=1
	    [test_univnewlines.py]=1 # Doesn't terminate
	    [test_urllib2_localnet.py]=1 # Doesn't terminate
	    [test_urllib2.py]=1 # test assertion failure
	    [test_urllib2net.py]=1 # Doesn't terminate
	    [test_warnings.py]=1
	    [test_xmlrpc.py]=1 # Doesn't terminate
	    [test_zipfile.py]=1 # too long
	    [test_zipfile64.py]=1
	    [test_zipimport.py]=1
	    [test_zipimport_support.py]=1
	    [test_zlib.py]=1
	)
	# 249 unit-test file in about 7 minutes and 44 seconds
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	fi
	;;
    3.5)
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
	    [test_dict.py]=1   #
	    [test_dictcomps.py]=1 # test assertion failure
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_dbm_gnu.py]=1   # Doesn't terminate
	    [test_decimal.py]=1
	    [test_descr.py]=1   # syntax error: Investigate
	    [test_doctest2.py]=1  #
	    [test_doctest.py]=1  #
	    [test_enum.py]=1  #
	    [test_exceptions.py]=1 # parse error
	    [test_fileinput.py]=1 # doesn't terminate
	    [test_format.py]=1
	    [file_eintr.py]=1
	    [test_fractions.py]=1 # doesn't terminate
	    [test_frame.py]=1 # doesn't terminate
	    [test_ftplib.py]=1 # doesn't terminate
	    [test_functools.py]=1 # doesn't terminate
	    [test_gc.py]=1 # doesn't terminate (test_trashcan_threads)
	    [test_generators.py]=1 # test assert failures
	    [test_glob.py]=1 #
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
	    [test_multiprocessing_fork.py]=1  # long
	    [test_multiprocessing_forkserver.py]=1  # long
	    [test_multiprocessing_spawn.py]=1 # long
	    [test_nntplib.py]=1 # too long 25 seconds
	    [test_optparse.py]=1 # Doesn't terminate test_positional_arg_and_variable_args
	    [test_ordered_dict.py]=1 # Doesn't terminate
	    [test_os.py]=1 # doesn't terminate
	    [test_peepholer.py]=1 # parse error
	    [test_pep352.py]=1 # test assertion error
	    [test_pep380.py]=1 # Investigate test assertion differ
	    [test_pickle.py]=1
	    [test_pkgimport.py]=1 # long
	    [test_poll.py]=1 # doesn't terminate on test_poll1
	    [test_poplib.py]=1
	    [test_print.py]=1
	    [test_pwd.py]=1   # Takes too long
	    [test_pydoc.py]=1 # test assertion: help text difference
	    [test_queue.py]=1 # Possibly parameter differences - investigate
	    [test_raise.py]=1 # Test assert error
	    [test_range.py]=1 # doesn't terminate
	    [test_readline.py]=1 # doesn't terminate
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
	    [test_threading.py]=1
	    [test_thread.py]=1
	    [test_threadsignals.py]=1 # doesn't terminate test_lock_acquire_retries
	    [test_timeout.py]=1
	    [test_traceback.py]=1
	    [test_typing.py]=1 # investigate syntax error
	    [test_unpack.py]=1 # weird, takes too long? Waiting on input?
	    [test_unpack_ex.py]=1 # doesn't terminate
	    [test_univnewlines.py]=1 # doesn't terminate
	    [test_urlparse.py]=1 # test assert error
	    [test_urllib2_localnet.py]=1  # doesn't terminate
	    [test_weakref.py]=1 # doesn't terminate test_threaded_weak_valued_consistency (__main__.MappingTestCase) ...
	    [test_xmlrpc.py]=1
	    [test_zipfile64.py]=1
	    [test_zipimport.py]=1
	    [test_zipimport_support.py]=1
	    [test_zlib.py]=1
	)
	    # About 240 remaining which can be done in about 10 minutes
	if (( batch )) ; then
	    # Fails in crontab environment?
	    # Figure out what's up here
	    SKIP_TESTS[test_bisect.py]=1
	    SKIP_TESTS[test_buffer.py]=1  # too long

	    SKIP_TESTS[test_exception_variations.py]=1
	    SKIP_TESTS[test_quopri.py]=1
	    SKIP_TESTS[test_ioctl.py]=1 # it fails on its own
	fi
	;;

    3.6)
	SKIP_TESTS=(
	    [test_aifc.py]=1  #
	    [test_asynchat.py]=1  # doesn't terminate
	    [test_asyncgen.py]=1  # parse error
	    [test_asyncore.py]=1  # doesn't terminate
	    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
	    [test_baseexception.py]=1 # test asert error
	    [test_bdb.py]=1  #
	    [test_binop.py]=1  # Doesn't terminate
	    [test_bisect.py]=1  # it fails on its own
	    [test_buffer.py]=1  # parse error
	    [test_builtin.py]=1  # Fails on its own
	    [test_bz2.py]=1  # testSeekBackwardsAcrossStreams (__main__.BZ2FileTest) ...  doesn't terminiate
	    [test_cmath.py]=1 # Investigate weird if control flow
	    [test_cmd_line.py]=1 # Interactive?
	    [test_codecs.py]=1
	    [test_colorsys.py]=1 # Doesn't terminate
	    [test_compile.py]=1
	    [test_concurrent_futures.py]=1 # Takes long
	    [test_configparser.py]=1  # Doesn't terminate
	    [test_contains.py]=1    # Code "while False: yield None" is optimized away in compilation
	    [test_contextlib.py]=1 # test assertion failure
	    [test_contextlib_async.py]=1 # Investigate
	    [test_coroutines.py]=1 # Parse error
	    [test_curses.py]=1 # Parse error
	    [test_dbm_gnu.py]=1   # Doesn't terminate
	    [test_decimal.py]=1
	    [test_descr.py]=1   # syntax error: Investigate
	    [test_dictcomps.py]=1   # We change line numbers - duh!
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_doctest2.py]=1  #
	    [test_doctest.py]=1  #
	    [test_enum.py]=1  #
	    [test_exceptions.py]=1   # parse error
	    [test_filecmp.py]=1   # parse error
	    [test_file_eintr.py]=1   # parse error
	    [test_fileinput.py]=1 # doesn't terminate
	    [test_finalization.py]=1
	    [test_fractions.py]=1 # doesn't terminate
	    [test_frame.py]=1 # doesn't terminate
	    [test_fstring.py]=1 # syntax error: Investigate
	    [test___future__.py]=1 # syntax error: Investigate
	    [test_gc.py]=1 # doesn't terminate (test_trashcan_threads)
	    [test_generators.py]=1 # test assert failures
	    [test_genexps.py]=1 #
	    [test_glob.py]=1 #
	    [test_grammar.py]=1 # parse error
	    [test_imaplib.py]=1
	    [test_inspect.py]=1 # Syntax error Investigate
	    [test_itertools.py]=1 #
	    [test_keywordonlyarg.py]=1 # Investigate
	    [test_long.py]=1 #
	    [test_lzma.py]=1 # doesn't terminate test_decompressor_chunks_maxsize
	    [test_marshal.py]=1 #
	    [test_math.py]=1 # call param Investigate
	    [test_metaclass.py]=1
	    [test_modulefinder.py]=1  # test assertion error
	    [test_multiprocessing_main_handling.py]=1 # takes too long -  11 seconds
	    [test test_nntplib.py]=1 # doesn't terminate
	    [test_nntplib.py]=1 # test takes too long to run: 31 seconds
	    [test_optparse.py]=1 # Doesn't terminate test_positional_arg_and_variable_args
	    [test_os.py]=1 # Doesn't terminate
	    [test_pdb.py]=1 # Probably introspection
	    [test_peepholer.py]=1
	    [test_pickle.py]=1
	    [test_platform.py]=1
	    [test_plistlib.py]=1
	    [test_poll.py]=1 # Takes too long 11 seconds
	    [test_poplib.py]=1
	    [test_pulldom.py]=1
	    [test_quopri.py]=1      # AssertionError: b'123=four' != '123=four'
	    [test_range.py]=1
	    [test_regrtest.py]=1 # test takes too long to run: 12 seconds
	    [test_robotparser.py]=1
	    [test_runpy.py]=1 # decompile takes too long?
	    [test_sched.py]=1
	    [test_scope.py]=1
	    [test_select.py]=1 # test takes too long to run: 11 seconds
	    [test_set.py]=1 # test assert failure and doesn't terminate
	    [test_shlex.py]=1 # Doesn't terminate
	    [test_smtpd.py]=1
	    [test_socket.py]=1 # long
	    [test_socketserver.py]=1
	    [test_string_literals.py]=1
	    [test_strptime.py]=1  # Doesn't terminate
	    [test_struct.py]=1  # Doesn't terminate
	    [test_subprocess.py]=1
	    [test_sys_settrace.py]=1 # parse error
	    [test_telnetlib.py]=1 # doesn't terminate
	    [test_threading.py]=1
	    [test_threadsignals.py]=1
	    [test_tokenize.py]=1 # test takes too long to run: 80 seconds
	    [test_timeout.py]=1
	    [test_traceback.py]=1
	    [test_tracemalloc.py]=1
	    [test_typing.py]=1 # investigate syntax error
	    [test_univnewlines.py]=1 # doesn't terminate
	    [test_urllib2_localnet.py]=1 # long
	    [test_venv.py]=1 # test takes too long to run: 13 seconds
	    [test_weakref.py]=1
	    [test_winreg.py]=1 # it fails on its own
	    [test_winsound.py]=1 # it fails on its own
	    [test_zipfile.py]=1 # Too long - 11 seconds
	    [test_zipfile64.py]=1
	    [test_zipimport.py]=1
	    [test_zipimport_support.py]=1
	    [test_zlib.py]=1
	)
	# 221 unit-test remaining files, Elapsed time about 16 minutes
	if (( batch )) ; then
	    SKIP_TESTS[test__locale.py]=1  # Wierd in batch environment
	fi
	;;
    3.7)
	SKIP_TESTS=(
	    [test_ast.py]=1  # Depends on comments in code
	    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
 	    [test_baseexception.py]=1  #
	    [test_bdb.py]=1  #
	    [test_buffer.py]=1  # parse error
	    [test_builtin.py]=1  # parser error
 	    [test_cmd_line.py]=1  # Interactive?
	    [test_cmd_line_script.py]=1
	    [test_collections.py]=1
	    [test_compare.py]=1
	    [test_compile.py]=1
	    [test_configparser.py]=1
	    [test_context.py]=1
	    [test_coroutines.py]=1 # Parse error
	    [test_crypt.py]=1 # Parse error
	    [test_curses.py]=1 # Parse error
	    [test_dataclasses.py]=1   # parse error
	    [test_datetime.py]=1   # Takes too long
	    [test_dbm_gnu.py]=1   # Takes too long
	    [test_decimal.py]=1   # Parse error
	    [test_descr.py]=1   # Parse error
	    [test_dictcomps.py]=1 # Bad semantics - Investigate
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_exceptions.py]=1   # parse error
	    [test_enumerate.py]=1   #
	    [test_enum.py]=1   #
	    [test_faulthandler.py]=1   # takes too long
	    [test_generators.py]=1  # improper decompile of assert i < n and (n-i) % 3 == 0
	    # ...
	)
	;;
    3.8)
	SKIP_TESTS=(
	    [test___all__.py]=1 # it fails on its own
	    [test_argparse.py]=1 #- it fails on its own
	    [test_asdl_parser.py]=1 # it fails on its own
	    [test_ast.py]=1  # Depends on comments in code
	    [test_atexit.py]=1  # The atexit test looks for specific comments in error lines
	    [test_baseexception.py]=1  #
	    [test_bdb.py]=1  #
	    [test_buffer.py]=1  # parse error
	    [test_builtin.py]=1  # parser error
	    [test_clinic.py]=1 # it fails on its own
	    [test_cmath.py]=1 # test assertion failure
 	    [test_cmd_line.py]=1  # Interactive?
	    [test_cmd_line_script.py]=1
	    [test_collections.py]=1
	    [test_compare.py]=1
	    [test_compileall.py]=1 # fails on its own
	    [test_compile.py]=1
	    [test_concurrent_futures.py]=1 # too long
	    [test_configparser.py]=1
	    [test_context.py]=1
	    [test_coroutines.py]=1 # Parse error
	    [test_codecs.py]=1
	    [test_code.py]=1 # Investigate
	    [test_complex.py]=1 # Investigate
	    [test_crypt.py]=1 # Parse error
	    [test_ctypes.py]=1 # it fails on its own
	    [test_curses.py]=1 # Parse error
	    [test_dataclasses.py]=1   # parse error
	    [test_datetime.py]=1   # Takes too long
	    [test_dbm_gnu.py]=1   # Takes too long
	    [test_dbm_ndbm.py]=1 # it fails on its own
	    [test_decimal.py]=1   # Parse error
	    [test_descr.py]=1   # Parse error
	    [test_devpoll.py]=1 # it fails on its own
	    [test_dictcomps.py]=1 # Bad semantics - Investigate
	    [test_dis.py]=1   # We change line numbers - duh!
	    [test_docxmlrpc.py]=1
	    [test_exceptions.py]=1   # parse error
	    [test_enumerate.py]=1   #
	    [test_enum.py]=1   #
	    [test_faulthandler.py]=1   # takes too long
	    [test_fcntl.py]=1
	    [test_fileinput.py]=1
	    [test_float.py]=1
	    [test_format.py]=1
	    [test_frame.py]=1
	    [test_fstring.py]=1 # Investigate
	    [test_ftplib.py]=1
	    [test_functools.py]=1
	    [test_gdb.py]=1 # it fails on its own
	    [test_generators.py]=1  # improper decompile of assert i < n and (n-i) % 3 == 0
	    [test_glob.py]=1  #
	    [test_grammar.py]=1
	    [test_grp.py]=1 # Doesn't terminate (killed)
	    [test_gzip.py]=1 # parse error
	    [test_hashlib.py]=1 # test assert failures
	    [test_httplib.py]=1 # parse error
	    [test_http_cookiejar.py]=1
	    [test_imaplib-3.7.py]=1
	    [test_idle.py]=1 # Probably installation specific
	    [test_io.py]=1 # test takes too long to run: 37 seconds
	    [test_imaplib.py]=1
	    [test_index.py]=1
	    [test_inspect.py]=1
	    [test_itertools.py]=1 # parse error
	    [test_keywordonlyarg.py]=1 # Investigate: parameter handling
	    [test_kqueue.py]=1 # it fails on its own
	    [test_lib2to3.py]=1 # it fails on its own
	    [test_long.py]=1 # investigate
	    [test_logging.py]=1 # test takes too long to run: 20 seconds
	    [test_mailbox.py]=1
	    [test_marshal.py]=1
	    [test_math.py]=1
	    [test_modulefinder.py]=1
	    [test_msilib.py]=1
	    [test_multiprocessing_fork.py]=1 # test takes too long to run: 62 seconds
	    [test_multiprocessing_forkserver.py]=1
	    [test_multiprocessing_spawn.py]=1
	    [test_normalization.py]=1 # probably control flow (uninitialized variable)
	    [test_nntplib.py]=1
	    [test_optparse.py]=1 # doesn't terminate (killed)
	    [test_os.py]=1 # probably control flow (uninitialized variable)
	    [test_ossaudiodev.py]=1 # it fails on its own
	    [test_pathlib.py]=1 # parse error
	    [test_pdb.py]=1 # Probably relies on comments
	    [test_peepholer.py]=1 # test assert error
	    [test_pickle.py]=1 # Probably relies on comments
	    [test_poll.py]=1
	    [test_poplib.py]=1
	    [test_pydoc.py]=1 # it fails on its own
	    [test_runpy.py]=1  #
	    [test_pkg.py]=1 # Investigate: lists differ
	    [test_pkgutil.py]=1 # Investigate:
	    [test_platform.py]=1 # probably control flow: uninitialized variable
	    [test_pow.py]=1 # probably control flow: test assertion failure
	    [test_pwd.py]=1 # killing - doesn't terminate
	    [test_regrtest.py]=1 # lists differ
	    [test_re.py]=1 # test assertion error
	    [test_richcmp.py]=1 # parse error
	    [test_select.py]=1 # test takes too long to run: 11 seconds
	    [test_selectors.py]=1
	    [test_shutil.py]=1 # fails on its own
	    [test_signal.py]=1 #
	    [test_slice.py]=1 # Investigate
	    [test_smtplib.py]=1 #
	    [test_socket.py]=1
	    [test_socketserver.py]=1
	    [test_sort.py]=1 # Probably control flow; unintialized varaible
	    [test_ssl.py]=1 # Probably control flow; unintialized varaible
	    [test_startfile.py]=1 # it fails on its own
	    [test_statistics.py]=1 # Probably control flow; unintialized varaible
	    [test_stat.py]=1 # test assertions failed
	    [test_string_literals.py]=1 # Investigate boolean parsing
	    [test_strptime.py]=1 # test assertions failed
	    [test_strtod.py]=1 # test assertions failed
	    [test_structmembers.py]=1 # test assertions failed
	    [test_struct.py]=1 # test assertions failed
	    [test_subprocess.py]=1
	    [test_sys_setprofile.py]=1 # test assertions failed
	    [test_sys_settrace.py]=1 # parse error
	    [test_tarfile.py]=1 # parse error
	    [test_threading.py]=1 #
	    [test_timeit.py]=1 # probably control flow uninitialized variable
	    [test_tk.py]=1  # test takes too long to run: 13 seconds
	    [test_tokenize.py]=1
	    [test_trace.py]=1  # it fails on its own
	    [test_traceback.py]=1 # Probably uses comment for testing
	    [test_tracemalloc.py]=1 #
	    [test_ttk_guionly.py]=1  # implementation specfic and test takes too long to run: 19 seconds
	    [test_typing.py]=1 # parse error
	    [test_types.py]=1 # parse error
	    [test_unicode.py]=1 # unicode thing
	    [test_urllib2.py]=1 #
	    [test_urllib2_localnet.py]=1 #
	    [test_urllibnet.py]=1 # probably control flow - uninitialized variable
	    [test_weakref.py]=1 # probably control flow - uninitialized variable
	    [test_with.py]=1 # probably control flow - uninitialized variable
	    [test_xml_dom_minicompat.py]=1 # parse error
	    [test_winconsoleio.py]=1 # it fails on its own
	    [test_winreg.py]=1 # it fails on its own
	    [test_winsound.py]=1 # it fails on its own
	    [test_zipfile.py]=1 # it fails on its own
	    [test_zipfile64.py]=1 #
	    )
	    # 268 Remaining unit-test files, Elapsed time about 11 minutes
	;;
    *)
	SKIP_TESTS=( [test_aepack.py]=1
		     [audiotests.py]=1
		     [test_dis.py]=1   # We change line numbers - duh!
		     [test_generators.py]=1  # I think string formatting of docstrings gets in the way. Not sure
		   )
	;;
esac

# Test directory setup
srcdir=$(dirname $me)
cd $srcdir
fulldir=$(pwd)

# pyenv version cleaning
for dir in .. ../.. ; do
    (cd $dir && [[ -r .python-version ]] && rm -v .python-version )
done

# DECOMPILER=uncompyle2
DECOMPILER=${DECOMPILER:-"$fulldir/../../bin/uncompyle6"}
TESTDIR=/tmp/test${PYVERSION}
if [[ -e $TESTDIR ]] ; then
    rm -fr $TESTDIR
fi

PYENV_ROOT=${PYENV_ROOT:-$HOME/.pyenv}
pyenv_local=$(pyenv local)
mkdir $TESTDIR || exit $?
cp -r ${PYENV_ROOT}/versions/${PYVERSION}.${MINOR}/lib/python${PYVERSION}/test $TESTDIR
cd $TESTDIR/test
pyenv local $FULLVERSION
export PYTHONPATH=$TESTDIR
export PATH=${PYENV_ROOT}/shims:${PATH}

# Run tests
typeset -i i=0
typeset -i allerrs=0
if [[ -n $1 ]] ; then
    files=$1
    typeset -a files_ary=( $(echo $1) )
    if (( ${#files_ary[@]} == 1 )) ; then
	SKIP_TESTS=()
    fi
else
    files=$(echo test_*.py)
fi

typeset -i ALL_FILES_STARTTIME=$(date +%s)
typeset -i skipped=0

for file in $files; do
    # AIX bash doesn't grok [[ -v SKIP... ]]
    if [[ ${SKIP_TESTS[$file]} == 1 ]] ; then
	((skipped++))
	continue
    fi

    # If the fails *before* decompiling, skip it!
    typeset -i STARTTIME=$(date +%s)
    if [ ! -r $file ]; then
	echo "Skipping test $file -- not readable. Does it exist?"
	continue
    elif ! python $file >/dev/null 2>&1 ; then
	echo "Skipping test $file -- it fails on its own"
	continue
    fi
    typeset -i ENDTIME=$(date +%s)
    typeset -i time_diff
    (( time_diff =  ENDTIME - STARTTIME))
    if (( time_diff > 10 )) ; then
	echo "Skipping test $file -- test takes too long to run: $time_diff seconds"
	continue
    fi

    ((i++))
    # (( i > 40 )) && break
    short_name=$(basename $file .py)
    decompiled_file=$short_name-${PYVERSION}.pyc
    $fulldir/compile-file.py $file && \
    mv $file{,.orig} && \
    echo ==========  $(date +%X) Decompiling $file ===========
    $DECOMPILER $decompiled_file > $file
    rc=$?
    if (( rc == 0 )) ; then
	echo ========== $(date +%X) Running $file ===========
	timeout_cmd python $file
	rc=$?
    else
	echo ======= Skipping $file due to compile/decompile errors ========
    fi
    (( rc != 0 && allerrs++ ))
    if (( STOP_ONERROR && rc )) ; then
	echo "** Ran $i tests before failure. Skipped $skipped test for known failures. **"
	exit $allerrs
    fi
done
typeset -i ALL_FILES_ENDTIME=$(date +%s)

(( time_diff =  ALL_FILES_ENDTIME - ALL_FILES_STARTTIME))

printf "Ran $i unit-test files, $allerrs errors; Elapsed time: "
displaytime $time_diff
echo "Skipped $skipped test for known failures."
cd $fulldir/../.. && pyenv local $FULLVERSION
exit $allerrs
