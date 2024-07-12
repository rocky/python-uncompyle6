SKIP_TESTS=(
    [test_aepack.py]=1 # it fails on its own
    [test_al.py]=1 # it fails on its own
    [test_applesingle.py]=1 # it fails on its own
    [test_bsddb185.py]=1 # it fails on its own
    [test_bsddb3.py]=1 # it fails on its own
    [test_bsddb.py]=1 # it fails on its own
    [test_cd.py]=1 # it fails on its own
    [test_cl.py]=1 # it fails on its own
    [test_codecmaps_cn.py]=1 # it fails on its own
    [test_codecmaps_hk.py]=1 # it fails on its own
    [test_codecmaps_jp.py]=1 # it fails on its own
    [test_codecmaps_kr.py]=1 # it fails on its own
    [test_codecmaps_tw.py]=1 # it fails on its own
    [test_curses.py]=1 # it fails on its own
    [test_dbm.py]=1 # it fails on its own
    [test_dl.py]=1 # it fails on its own
    [test_gdbm.py]=1 # it fails on its own
    [test_gl.py]=1 # it fails on its own
    [test_imageop.py]=1 # it fails on its own
    [test_imgfile.py]=1 # it fails on its own
    [test_linuxaudiodev.py]=1 # it fails on its own
    [test_macfs.py]=1 # it fails on its own
    [test_macostools.py]=1 # it fails on its own
    [test_nis.py]=1 # it fails on its own
    [test_normalization.py]=1 # it fails on its own
    [test_ossaudiodev.py]=1 # it fails on its own
    [test_pep277.py]=1 # it fails on its own
    [test_plistlib.py]=1 # it fails on its own
    [test_rgbimg.py]=1 # it fails on its own
    [test_scriptpackages.py]=1 # it fails on its own
    [test_socket_ssl.py]=1 # it fails on its own
    [test_sunaudiodev.py]=1 # it fails on its own
    [test_support.py]=1 # it fails on its own
    [test_tcl.py]=1 # it fails on its own
    [test_urllib2net.py]=1 # it fails on its own
    [test_urllibnet.py]=1 # it fails on its own
    [test_winreg.py]=1 # it fails on its own
    [test_winsound.py]=1 # it fails on its own
    [test_zlib.py]=1 # it fails on its own
    [test_decimal.py]=1  # fails on its own - no module named test_support
    [test_dis.py]=1   # We change line numbers - duh!
    [test_generators.py]=1  # fails on its own - no module named test_support
    # [test_grammar.py]=1    # fails on its own - no module tests.test_support
    [test_grp.py]=1      # Long test - might work Control flow?
    [test_socketserver.py]=1 # -- test takes too long to run: 40 seconds
    [test_threading.py]=1 # test takes too long to run: 11 seconds
    [test_thread.py]=1 # test takes too long to run: 36 seconds
    [test_trace.py]=1 # Long test - works
)
 # About 243 files, 0 in 19 minutes
