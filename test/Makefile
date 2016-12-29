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
check-2.6 check-2.7: check-bytecode-2 check-bytecode-3 check-bytecode-1  check-2.7-ok

#: Run working tests from Python 3.0
check-3.0: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.0 --weak-verify $(COMPILE)

#: Run working tests from Python 3.1
check-3.1: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.1 --weak-verify $(COMPILE)

#: Run working tests from Python 3.2
check-3.2: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.2 --weak-verify $(COMPILE)

#: Run working tests from Python 3.3
check-3.3: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.3 --verify $(COMPILE)

#: Run working tests from Python 3.4
check-3.4: check-bytecode check-3.4-ok check-2.7-ok
	$(PYTHON) test_pythonlib.py --bytecode-3.4 --verify $(COMPILE)

#: Run working tests from Python 3.5
check-3.5: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.5 --verify $(COMPILE)

#: Run working tests from Python 3.6
check-3.6: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.6 --verify $(COMPILE)

#: Check deparsing only, but from a different Python version
check-disasm:
	$(PYTHON) dis-compare.py

#: Check deparsing bytecode 1.x only
check-bytecode-1:
	$(PYTHON) test_pythonlib.py --bytecode-1.5

#: Check deparsing bytecode 2.x only
check-bytecode-2:
	$(PYTHON) test_pythonlib.py \
	--bytecode-2.1 --bytecode-2.2 --bytecode-2.3 --bytecode-2.4 \
        --bytecode-2.5 --bytecode-2.6 --bytecode-2.7 --bytecode-pypy2.7

#: Check deparsing bytecode 3.x only
check-bytecode-3:
	$(PYTHON) test_pythonlib.py --bytecode-3.0 \
       --bytecode-3.1 --bytecode-3.2 --bytecode-3.3 \
       --bytecode-3.4 --bytecode-3.5 --bytecode-pypy3.2

#: Check deparsing bytecode that works running Python 2 and Python 3
check-bytecode: check-bytecode-3
	$(PYTHON) test_pythonlib.py \
	--bytecode-2.1 --bytecode-2.2 --bytecode-2.3 --bytecode-2.4 \
        --bytecode-2.5 --bytecode-2.6 --bytecode-2.7 \
        --bytecode-pypy2.7 --bytecode-1


#: Check deparsing Python 2.1
check-bytecode-2.1:
	$(PYTHON) test_pythonlib.py --bytecode-2.1

#: Check deparsing Python 2.2
check-bytecode-2.2:
	$(PYTHON) test_pythonlib.py --bytecode-2.2

#: Check deparsing Python 2.3
check-bytecode-2.3:
	$(PYTHON) test_pythonlib.py --bytecode-2.3

#: Check deparsing Python 2.4
check-bytecode-2.4:
	$(PYTHON) test_pythonlib.py --bytecode-2.4

#: Check deparsing Python 2.5
check-bytecode-2.5:
	$(PYTHON) test_pythonlib.py --bytecode-2.5

#: Check deparsing Python 2.6
check-bytecode-2.6:
	$(PYTHON) test_pythonlib.py --bytecode-2.6 --weak-verify

#: Check deparsing Python 2.7
check-bytecode-2.7:
	$(PYTHON) test_pythonlib.py --bytecode-2.7 --verify

#: Check deparsing Python 3.0
check-bytecode-3.0:
	$(PYTHON) test_pythonlib.py --bytecode-3.0

#: Check deparsing Python 3.1
check-bytecode-3.1:
	$(PYTHON) test_pythonlib.py --bytecode-3.1

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

#: Check deparsing Python 3.6
check-bytecode-3.6:
	$(PYTHON) test_pythonlib.py --bytecode-3.6

#: short tests for bytecodes only for this version of Python
check-native-short:
	$(PYTHON) test_pythonlib.py --bytecode-$(PYTHON_VERSION) --verify $(COMPILE)

#: Run longer Python 2.6's lib files known to be okay
check-2.6-ok:
	$(PYTHON) test_pythonlib.py --ok-2.6 --verify $(COMPILE)

#: Run longer Python 2.7's lib files known to be okay
check-2.7-ok:
	$(PYTHON) test_pythonlib.py --ok-2.7 --verify $(COMPILE)

#: Run longer Python 3.2's lib files known to be okay
check-3.2-ok:
	$(PYTHON) test_pythonlib.py --ok-3.2 --verify $(COMPILE)

#: Run longer Python 3.4's lib files known to be okay
check-3.4-ok:
	$(PYTHON) test_pythonlib.py --ok-3.4 --verify $(COMPILE)

#: PyPy of some sort. E.g. [PyPy 5.0.1 with GCC 4.8.4]
# Skip for now
2.6:

#: PyPy 5.0.x with Python 2.7 ...
pypy-2.7 5.0 5.3:
	$(PYTHON) test_pythonlib.py --bytecode-pypy2.7 --verify

#: PyPy 2.4.x with Python 3.2 ...
pypy-3.2 2.4:
	$(PYTHON) test_pythonlib.py --bytecode-pypy3.2 --verify

clean: clean-py-dis clean-dis clean-unverified

clean-dis:
	find . -name '*_dis' -exec rm -v '{}' ';'

clean-unverified:
	find . -name '*_unverified' -exec rm -v '{}' ';'

#: Clean temporary compile/decompile/verify directories in /tmp
clean-py-dis:
	rm -fr /tmp/py-dis-* || true
