# Compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= git2cl
PYTHON ?= python
PYTHON3 ?= python3
RM      ?= rm
LINT    = flake8

#EXTRA_DIST=ipython/ipy_trepan.py trepan
PHONY=all check check-2.7 check-3.4 \
     clean distcheck pytest check-long check-short \
     dist distclean lint flake8 test rmChangeLog clean_pyc \
     2.6 5.0 5.3 5.6 5.8 7.2 7.3 check-short

TEST_TYPES=check-long check-short check-2.7 check-3.4

#: Default target - same as "check"
all: check

# Run all tests
check:
	@PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	$(MAKE) check-$$PYTHON_VERSION

# Run all quick tests
check-short: pytest
	$(MAKE) -C test check-short

# Note for 2.6 use <=3.0.1 see requirements-dev.txt
#: Tests for Python 2.7, 3.3 and 3.4
check-2.6 check-2.7 check-3.3 check-3.4 check-3.5: pytest
	$(MAKE) -C test $@

#: Tests for Python 3.2 and 3.5 - pytest doesn't work here
# Or rather 3.5 doesn't work not on Travis
check-3.0 check-3.1 check-3.2 check-3.6:
	$(MAKE) -C test $@

check-3.7: pytest
	$(MAKE) -C test check

check-3.8 check-3.9 check-3.10 check-3.11 check-3.12 check-3.13:
	$(MAKE) -C test check-3.8

#:PyPy 2.6.1 PyPy 5.0.1, or PyPy 5.8.0-beta0
# Skip for now
2.6 5.0 5.3 5.6 5.8:

#:PyPy pypy3-2.4.0 Python 3.6.1:
7.1 pypy-3.2 2.4:
	$(MAKE) -C test $@

#:PyPy versions
7.2 7.3:
	$(MAKE) -C test $@

#:pyston versions
2.3:
	$(MAKE) -C test $@

#: Run py.test tests
pytest:
	$(MAKE) -C pytest check

#: Clean up temporary files and .pyc files
clean: clean_pyc

#: Create source (tarball) and wheel distribution
dist: distcheck
	$(PYTHON) ./setup.py sdist bdist_wheel

# perform some checks on the package via setup.py
distcheck:
	$(PYTHON) ./setup.py check

#: Remove .pyc files
clean_pyc:
	( cd uncompyle6 && $(RM) -f *.pyc */*.pyc )

#: Create source tarball
sdist:
	$(PYTHON) ./setup.py sdist


#: Style check. Set env var LINT to pyflakes, flake, or flake8
lint: flake8

# Check StructuredText long description formatting
check-rst:
	$(PYTHON) setup.py --long-description | rst2html.py > python3-trepan.html

#: Lint program
flake8:
	$(LINT) uncompyle6

#: Create binary egg distribution
bdist_egg:
	$(PYTHON) ./setup.py bdist_egg


#: Create binary wheel distribution
wheel:
	$(PYTHON) ./setup.py bdist_wheel


# It is too much work to figure out how to add a new command to distutils
# to do the following. I'm sure distutils will someday get there.
DISTCLEAN_FILES = build dist *.pyc

#: Remove ALL derived files
distclean: clean
	-rm -fvr $(DISTCLEAN_FILES) || true
	-find . -name \*.pyc -exec rm -v {} \;
	-find . -name \*.egg-info -exec rm -vr {} \;

#: Install package locally
verbose-install:
	$(PYTHON) ./setup.py install

#: Install package locally without the verbiage
install:
	$(PYTHON) ./setup.py install >/dev/null

rmChangeLog:
	rm ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@

.PHONY: $(PHONY)
