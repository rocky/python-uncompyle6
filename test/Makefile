PHONY=check clean dist distclean test test-unit test-functional rmChangeLog clean_pyc nosetests

GIT2CL ?= git2cl
PYTHON ?= python

# Set COMILE='--compile' to force compilation before check
COMPILE ?=

#: Run all tests
check: check-short check-2.7-ok

#: Run quick tests
check-short:
	$(PYTHON) test_pythonlib.py --base-2.7 --verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-2.5

#: Run longer Python 2.7's lib files known to be okay
check-2.7-ok:
	$(PYTHON) test_pythonlib.py --ok-2.7 --verify $(COMPILE)

clean: clean-py-dis clean-dis

clean-dis:
	find . -name '*_dis' -exec rm -v '{}' ';'

#: Clean temporary compile/decompile/verify direcotries in /tmp
clean-py-dis:
	rm -fr /tmp/py-dis-* || true
