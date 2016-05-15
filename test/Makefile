PHONY=check clean dist distclean test test-unit test-functional rmChangeLog clean_pyc nosetests

GIT2CL ?= git2cl
PYTHON ?= python

PYTHON_VERSION = $(shell $(PYTHON) -V | cut -d ' ' -f 2 | cut -d'.' -f1,2)
NATIVE_CHECK = check-$(PYTHON_VERSION)

# Set COMPILE='--compile' to force compilation before check
COMPILE ?=

# Run short tests
check-short:
	@$(PYTHON) -V && PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	$(MAKE) check-bytecode

# Run all tests
check:
	@$(PYTHON) -V && PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	$(MAKE) check-$$PYTHON_VERSION

#: Run working tests from Python 2.6 or 2.7
check-2.6 check-2.7: check-bytecode check-2.7-ok

#: Run working tests from Python 3.2
check-3.2: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.2 --verify $(COMPILE)

#: Run working tests from Python 3.3
check-3.3: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.3 --verify $(COMPILE)

#: Run working tests from Python 3.5
check-3.5: check-bytecode

#: Run working tests from Python 3.4
check-3.4: check-bytecode check-3.4-ok check-2.7-ok
	$(PYTHON) test_pythonlib.py --bytecode-3.4 --verify $(COMPILE)

#: Check deparsing only, but from a different Python version
check-disasm:
	$(PYTHON) dis-compare.py

#: Check deparsing bytecode only
check-bytecode-2:
	$(PYTHON) test_pythonlib.py --bytecode-2.5 --bytecode-2.6 --bytecode-2.7

#: Check deparsing bytecode only
check-bytecode:
	$(PYTHON) test_pythonlib.py --bytecode-2.5 --bytecode-2.6 --bytecode-2.7 \
        --bytecode-3.2 --bytecode-3.3 --bytecode-3.4 --bytecode-3.5

#: Check deparsing Python 2.5
check-bytecode-2.5:
	$(PYTHON) test_pythonlib.py --bytecode-2.5

#: Check deparsing Python 2.6
check-bytecode-2.6:
	$(PYTHON) test_pythonlib.py --bytecode-2.6

#: Check deparsing Python 2.7
check-bytecode-2.7:
	$(PYTHON) test_pythonlib.py --bytecode-2.7

#: Check deparsing Python 3.2
check-bytecode-3.2:
	$(PYTHON) test_pythonlib.py --bytecode-3.2

#: Check deparsing Python 3.3
check-bytecode-3.3:
	$(PYTHON) test_pythonlib.py --bytecode-3.3

#: Check deparsing Python 3.4
check-bytecode-3.4:
	$(PYTHON) test_pythonlib.py --bytecode-3.4

#: Check deparsing Python 3.5
check-bytecode-3.5:
	$(PYTHON) test_pythonlib.py --bytecode-3.5

#: short tests for bytecodes only for this version of Python
check-native-short:
	$(PYTHON) test_pythonlib.py --bytecode-$(PYTHON_VERSION) --verify $(COMPILE)

#: Run longer Python 2.7's lib files known to be okay
check-2.7-ok:
	$(PYTHON) test_pythonlib.py --ok-2.7 --verify $(COMPILE)

#: Run longer Python 3.2's lib files known to be okay
check-3.2-ok:
	$(PYTHON) test_pythonlib.py --ok-3.2 --verify $(COMPILE)

#: Run longer Python 3.4's lib files known to be okay
check-3.4-ok:
	$(PYTHON) test_pythonlib.py --ok-3.4 --verify $(COMPILE)

clean: clean-py-dis clean-dis clean-unverified

clean-dis:
	find . -name '*_dis' -exec rm -v '{}' ';'

clean-unverified:
	find . -name '*_unverified' -exec rm -v '{}' ';'

#: Clean temporary compile/decompile/verify direcotries in /tmp
clean-py-dis:
	rm -fr /tmp/py-dis-* || true
