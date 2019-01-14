PHONY=check clean dist distclean test test-unit test-functional rmChangeLog clean_pyc nosetests \
      check-bytecode-1  check-bytecode-1.3 check-bytecode-1.4 check-bytecode-1.5 \
      check-bytecode-2 check-bytecode-3 check-bytecode-3-short \
      check-bytecode-2.2 check-byteocde-2.3 check-bytecode-2.4 \
      check-short check-2.6 check-2.7 check-3.0 check-3.1 check-3.2 check-3.3 \
      check-3.4 check-3.5 check-3.6 check-3.7 check-5.6 5.6 5.8 \
      grammar-coverage-2.5 grammar-coverage-2.6 grammar-coverage-2.7 \
      grammar-coverage-3.1 grammar-coverage-3.2 grammar-coverage-3.3 \
      grammar-coverage-3.4 grammar-coverage-3.5 grammar-coverage-3.6 \
      grammar-coverage-3.7

GIT2CL ?= git2cl
PYTHON ?= python

PYTHON_VERSION = $(shell $(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2)
NATIVE_CHECK = check-$(PYTHON_VERSION)

# Set COMPILE='--compile' to force compilation before check
COMPILE ?=
COVER_DIR=../tmp/grammar-cover

# Run short tests
check-short:
	@$(PYTHON) -V && PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	$(MAKE) check-bytecode-short

# Run all tests
check:
	$(MAKE) check-$(PYTHON_VERSION)

#: Run working tests from Python 2.6 or 2.7
check-2.6 check-2.7: check-bytecode-2 check-bytecode-3 check-bytecode-1 check-native-short

#: Run working tests from Python 3.0
check-3.0: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.0 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.0-run --verify-run

#: Run working tests from Python 3.1
check-3.1: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.1 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.1-run --verify-run

#: Run working tests from Python 3.2
check-3.2: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.2 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.2-run --verify-run

#: Run working tests from Python 3.3
check-3.3: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.3 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.3-run --verify-run

#: Run working tests from Python 3.4
check-3.4: check-bytecode check-3.4-ok check-2.7-ok
	$(PYTHON) test_pythonlib.py --bytecode-3.4 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.4-run --verify-run

#: Run working tests from Python 3.5
check-3.5: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.5 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.5-run --verify-run

#: Run working tests from Python 3.6
check-3.6: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.6 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.6-run --verify-run

#: Run working tests from Python 3.7
check-3.7: check-bytecode
	$(PYTHON) test_pythonlib.py --bytecode-3.7 --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-3.7-run --verify-run

# FIXME
#: this is called when running under pypy3.5-5.8.0 or pypy2-5.6.0
5.8 5.6:

#: Check deparsing only, but from a different Python version
check-disasm:
	$(PYTHON) dis-compare.py

#: Check deparsing bytecode 1.x only
check-bytecode-1: check-bytecode-1.4 check-bytecode-1.5

#: Check deparsing bytecode 2.x only
check-bytecode-2:
	$(PYTHON) test_pythonlib.py \
	--bytecode-2.1 --bytecode-2.2 --bytecode-2.3 --bytecode-2.4 \
        --bytecode-2.5 --bytecode-2.6 --bytecode-2.7 --bytecode-pypy2.7

#: Check deparsing bytecode 3.x only
check-bytecode-3:
	$(PYTHON) test_pythonlib.py --bytecode-3.0 \
	--bytecode-3.1 --bytecode-3.2 --bytecode-3.3 \
	--bytecode-3.4 --bytecode-3.5 --bytecode-3.6 --bytecode-3.7 \
	--bytecode-pypy3.2

#: Check deparsing on selected bytecode 3.x
check-bytecode-3-short:
	$(PYTHON) test_pythonlib.py \
       --bytecode-3.4 --bytecode-3.5 --bytecode-3.6

#: Check deparsing bytecode on all Python 2 and Python 3 versions
check-bytecode: check-bytecode-3
	$(PYTHON) test_pythonlib.py \
	--bytecode-1.3 --bytecode-1.4 --bytecode-1.5 \
        --bytecode-2.2 --bytecode-2.3 --bytecode-2.4 \
	--bytecode-2.1 --bytecode-2.2 --bytecode-2.3 --bytecode-2.4 \
        --bytecode-2.5 --bytecode-2.6 --bytecode-2.7 \
        --bytecode-pypy2.7


#: Check deparsing bytecode on selected Python 2 and Python 3 versions
check-bytecode-short: check-bytecode-3-short
	$(PYTHON) test_pythonlib.py \
        --bytecode-2.6 --bytecode-2.7 --bytecode-pypy2.7


#: Check deparsing bytecode 1.3 only
check-bytecode-1.3:
	$(PYTHON) test_pythonlib.py --bytecode-1.3

#: Check deparsing bytecode 1.4 only
check-bytecode-1.4:
	$(PYTHON) test_pythonlib.py --bytecode-1.4

#: Check deparsing bytecode 1.5 only
check-bytecode-1.5:
	$(PYTHON) test_pythonlib.py --bytecode-1.5

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

#: Get grammar coverage for Python 2.4
grammar-coverage-2.4:
	-rm $(COVER_DIR)/spark-grammar-24.cover
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.4.cover $(PYTHON) test_pythonlib.py --bytecode-2.4
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.4.cover $(PYTHON) test_pyenvlib.py --2.4.6 --max= 800

#: Get grammar coverage for Python 2.5
grammar-coverage-2.5:
	-rm $(COVER_DIR)/spark-grammar-2.5.cover || true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.5.cover $(PYTHON) test_pythonlib.py --bytecode-2.5
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.5.cover $(PYTHON) test_pyenvlib.py --2.5.6 --max=800

#: Get grammar coverage for Python 2.6
grammar-coverage-2.6:
	-rm $(COVER_DIR)/spark-grammar-2.6.cover || true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.6.cover $(PYTHON) test_pythonlib.py --bytecode-2.6
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.6.cover $(PYTHON) test_pyenvlib.py --2.6.9 --max=800

#: Get grammar coverage for Python 2.7
grammar-coverage-2.7:
	-rm $(COVER_DIR)/spark-grammar-2.7.cover || true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.7.cover $(PYTHON) test_pythonlib.py --bytecode-2.7
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-2.7.cover $(PYTHON) test_pyenvlib.py --2.7.14 --max=600

#: Get grammar coverage for Python 3.0
grammar-coverage-3.0:
	-rm $(COVER_DIR)/spark-grammar-30.cover

SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-30.cover $(PYTHON) test_pythonlib.py --bytecode-3.1
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-30.cover $(PYTHON) test_pyenvlib.py --3.0.1

#: Get grammar coverage for Python 3.1
grammar-coverage-3.1:
	-rm $(COVER_DIR)/spark-grammar-3.1.cover
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.1.cover $(PYTHON) test_pythonlib.py --bytecode-3.1
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.1.cover $(PYTHON) test_pyenvlib.py --3.1.5

#: Get grammar coverage for Python 3.2
grammar-coverage-3.2:
	-rm $(COVER_DIR)/spark-grammar-3.2.cover || true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.2.cover $(PYTHON) test_pythonlib.py --bytecode-3.2
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.2.cover $(PYTHON) test_pyenvlib.py --3.2.6

#: Get grammar coverage for Python 3.3
grammar-coverage-3.3:
	-rm $(COVER_DIR)/spark-grammar-3.3.cover || true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.3.cover $(PYTHON) test_pythonlib.py --bytecode-3.3
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.3.cover $(PYTHON) test_pyenvlib.py --3.3.7 --max=800

#: Get grammar coverage for Python 3.4
grammar-coverage-3.4:
	-rm $(COVER_DIR)/spark-grammar-3.4.cover || true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.4.cover $(PYTHON) test_pythonlib.py --bytecode-3.4
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.4.cover $(PYTHON) test_pyenvlib.py --3.4.8 --max=800

#: Get grammar coverage for Python 3.5
grammar-coverage-3.5:
	rm $(COVER_DIR)/spark-grammar-3.5.cover || /bin/true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.5.cover $(PYTHON) test_pythonlib.py --bytecode-3.5
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.5.cover $(PYTHON) test_pyenvlib.py --3.5.5 --max=450

#: Get grammar coverage for Python 3.6
grammar-coverage-3.6:
	rm $(COVER_DIR)/spark-grammar-3.6.cover || /bin/true
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.6.cover $(PYTHON) test_pythonlib.py --bytecode-3.6
	SPARK_PARSER_COVERAGE=$(COVER_DIR)/spark-grammar-3.6.cover $(PYTHON) test_pyenvlib.py --3.6.4 --max=280

#: Check deparsing Python 2.6
check-bytecode-2.6:
	$(PYTHON) test_pythonlib.py --bytecode-2.6 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-2.6-run --verify-run

#: Check deparsing Python 2.7
check-bytecode-2.7:
	$(PYTHON) test_pythonlib.py --bytecode-2.7 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-2.7-run --verify-run

#: Check deparsing Python 3.0
check-bytecode-3.0:
	$(PYTHON) test_pythonlib.py --bytecode-3.0 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.0-run --verify-run

#: Check deparsing Python 3.1
check-bytecode-3.1:
	$(PYTHON) test_pythonlib.py --bytecode-3.1 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.1-run --verify-run

#: Check deparsing Python 3.2
check-bytecode-3.2:
	$(PYTHON) test_pythonlib.py --bytecode-3.2 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.2-run --verify-run

#: Check deparsing Python 3.3
check-bytecode-3.3:
	$(PYTHON) test_pythonlib.py --bytecode-3.3 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.3-run --verify-run

#: Check deparsing Python 3.4
check-bytecode-3.4:
	$(PYTHON) test_pythonlib.py --bytecode-3.4 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.4-run --verify-run

#: Check deparsing Python 3.5
check-bytecode-3.5:
	$(PYTHON) test_pythonlib.py --bytecode-3.5 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.5-run --verify-run

#: Check deparsing Python 3.6
check-bytecode-3.6:
	$(PYTHON) test_pythonlib.py --bytecode-3.6 --weak-verify
	$(PYTHON) test_pythonlib.py --bytecode-3.6-run --verify-run

#: Check deparsing Python 3.7
check-bytecode-3.7:
	$(PYTHON) test_pythonlib.py --bytecode-3.7 --weak-verify

#: short tests for bytecodes only for this version of Python
check-native-short:
	$(PYTHON) test_pythonlib.py --bytecode-$(PYTHON_VERSION) --weak-verify $(COMPILE)
	$(PYTHON) test_pythonlib.py --bytecode-$(PYTHON_VERSION)-run --verify-run $(COMPILE)

#: Run longer Python 2.6's lib files known to be okay
check-2.6-ok:
	$(PYTHON) test_pythonlib.py --ok-2.6 --weak-verify $(COMPILE)

#: Run longer Python 2.7's lib files known to be okay
check-2.7-ok:
	$(PYTHON) test_pythonlib.py --ok-2.7 --weak-verify $(COMPILE)

#: Run longer Python 3.2's lib files known to be okay
check-3.2-ok:
	$(PYTHON) test_pythonlib.py --ok-3.2 --weak-verify $(COMPILE)

#: Run longer Python 3.4's lib files known to be okay
check-3.4-ok:
	$(PYTHON) test_pythonlib.py --ok-3.4 --weak-verify $(COMPILE)

#: PyPy of some sort. E.g. [PyPy 5.0.1 with GCC 4.8.4]
# Skip for now
2.6:

#: PyPy 5.0.x with Python 2.7 ...
pypy-2.7 5.0 5.3 6.0:
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
