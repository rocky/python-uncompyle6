PHONY=check clean dist distclean test test-unit test-functional rmChangeLog clean_pyc nosetests

GIT2CL ?= git2cl
PYTHON ?= python

PYTHON_VERSION = $(shell $(PYTHON) -V | cut -d ' ' -f 2 | cut -d'.' -f1,2)
NATIVE_CHECK = check-$(PYTHON_VERSION)

# Set COMPILE='--compile' to force compilation before check
COMPILE ?=

#: Run working tests from Python 2.7
check-2.7: check-short-2.7 check-bytecode check-2.7-ok

#: Run working tests from Python 3.4
check-3.4: check-short-2.7 check-bytecode check-native-short

check:
	@echo "For now, use check-2.7 or check.3.4" && false

## FIXME: there is a bug in our code that I don't
## find in uncompyle2 that causes this to fail.
## parsing.
## the failing program works if run by itself.
## This leads me to believe the problem is an
## initialization bug?

#: Check deparsing only, but from a different Python version
check-disasm:
	$(PYTHON) dis-compare.py

#: Check deparsing only, but from a different Python version
check-bytecode:
	$(PYTHON) test_pythonlib.py --bytecode-2.5

#: short tests for bytecodes only for this version of Python
check-native-short:
	$(PYTHON) test_pythonlib.py --bytecode-$(PYTHON_VERSION) --verify $(COMPILE)

check-short-2.7:
	$(PYTHON) test_pythonlib.py --bytecode-2.7 --verify $(COMPILE)

#: Run longer Python 2.7's lib files known to be okay
check-2.7-ok:
	$(PYTHON) test_pythonlib.py --ok-2.7 --verify $(COMPILE)

clean: clean-py-dis clean-dis clean-unverified

clean-dis:
	find . -name '*_dis' -exec rm -v '{}' ';'

clean-unverified:
	find . -name '*_unverified' -exec rm -v '{}' ';'

#: Clean temporary compile/decompile/verify direcotries in /tmp
clean-py-dis:
	rm -fr /tmp/py-dis-* || true
