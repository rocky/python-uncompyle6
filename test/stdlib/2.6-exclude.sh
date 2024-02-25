SKIP_TESTS=(
    # ifelsestmt is borked in:
    #   if filename == 'srcfile':
    #      return srcfile
    #   if filename == 'destfile':
    #      return destfile
    #   assert 0  # shouldn't reach here.
    # [test_shutil.py]=1 # OK but needs PYTHON=pytest

    [test___all__.py]=1 # it fails on its own
    [test_aepack.py]=1 # No module macostools
    [test_al.py]=1 # No module macostools
    [test_anydbm.py]=pytest
    [test_applesingle.py]=1 # No module macostools
    [test_bsddb185.py]=1 # it fails on its own
    [test_bsddb3.py]=1 # it fails on its own
    [test_bsddb.py]=1 # No module _bsdb

    [test_cd.py]=1 # i# No module cl
    [test_cl.py]=1 # it fails on its own
    [test_cmath.py]=pytest
    [test_codecmaps_cn.py]=1 # it fails on its own
    [test_codecmaps_jp.py]=1 # it fails on its own
    [test_codecmaps_kr.py]=1 # it fails on its own
    [test_codecmaps_tw.py]=1 # it fails on its own
    [test_commands.py]=1 # it fails on its own
    [test_curses.py]=1 # needs libncurses.so.5

    [test_dbm.py]=1 # it fails on its own
    [test_descr.py]=1
    [test_doctest.py]=1    #
    [test_dis.py]=1        # We change line numbers - duh!
    [test_dl.py]=1 # it fails on its own

    [test_file.py]=1 # it fails on its own
    [test_future5.py]=pytest

    [test_generators.py]=pytest
    [test_gl.py]=1 # it fails on its own
    [test_grp.py]=pytest

    [test_imageop.py]=1 # it fails on its own
    [test_imaplib.py]=1 # it fails on its own
    [test_imgfile.py]=1 # it fails on its own
    [test_ioctl.py]=pytest

    [test_kqueue.py]=1 # it fails on its own

    [test_linuxaudiodev.py]=1 # it fails on its own

    [test_macos.py]=1 # it fails on its own
    [test_macostools.py]=1 # it fails on its own
    [test_mailbox.py]=1 # FIXME: release 3.6.2 may have worked

    # [test_normalization.py]=1 # it fails on its own

    [test_ossaudiodev.py]=1 # it fails on its own

    [test_pep277.py]=1 # it fails on its own
    [test_pyclbr.py]=1 # it fails on its own
    [test_py3kwarn.py]=1 # it fails on its own

    [test_scriptpackages.py]=1 # it fails on its own
    [test_select.py]=1 # test takes too long to run: 11 seconds

    [test_signal.py]=1 # takes more than 15 seconds to run
    [test_socket.py]=1 # test takes too long to run: 12 seconds
    [test_startfile.py]=1 # it fails on its own
    [test_structmembers.py]=1 # it fails on its own
    [test_sunaudiodev.py]=1 # it fails on its own
    [test_support.py]=1 # # it fails on it s own

    [test_threading.py]=1  # fails on its own?
    [test_trace.py]=1  # Line numbers are expected to be different

    [test_urllib2_localnet.py]=1 # test takes too long to run: 12 seconds
    [test_urllib2net.py]=1 # test takes too long to run: 11 seconds
    [test_urllibnet.py]=1 # it fails on its own


    [test_whichdb.py]=1 # it fails on its own
    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own

    [test_zipimport_support.py]=pytest # expected test to raise ImportError
    [test_zipfile.py]=pytest  # Skip Long test
    # .pyenv/versions/2.6.9/lib/python2.6/lib2to3/refactor.pyc
    # .pyenv/versions/2.6.9/lib/python2.6/pyclbr.pyc
)
# About 305 unit-test files in about 12 minutes

if (( BATCH )) ; then
    # Fails in crontab environment?
    # Figure out what's up here
    SKIP_TESTS[test_aifc.py]=1
    SKIP_TESTS[test_array.py]=1

    # SyntaxError: Non-ASCII character '\xdd' in file test_base64.py on line 153, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
    SKIP_TESTS[test_base64.py]=1
    SKIP_TESTS[test_decimal.py]=1 # Might be a POWER math thing

    # output indicates expected == output, but this fails anyway.
    # Maybe the underlying encoding is subtlely different so it
    # looks the same?
fi
