# Had bug in 3.x in not having semantic importlist rule
def main(osp, Mfile, mainpyfile, dbg=None):
    try:
        from xdis import load_module, PYTHON_VERSION, IS_PYPY
        return PYTHON_VERSION, IS_PYPY, load_module
    except:
        pass
