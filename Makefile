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
PHONY=all check clean pytest check-long dist distclean lint flake8 test rmChangeLog clean_pyc

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

#: Tests for Python 2.7, 3.3 and 3.4
check-2.7 check-3.3 check-3.4: pytest
	$(MAKE) -C test $@

#: Tests for Python 3.2 and 3.5 - pytest doesn't work here
# Or rather 3.5 doesn't work not on Travis
check-3.0 check-3.1 check-3.2 check-3.5 check-3.6:
	$(MAKE) -C test $@

#:Tests for Python 2.6 (doesn't have pytest)
check-2.6:
	$(MAKE) -C test $@

#:PyPy 2.6.1 or PyPy 5.0.1
# Skip for now
2.6 5.0 5.3:

#:PyPy pypy3-2.4.0 Python 3:
pypy-3.2 2.4:
	$(MAKE) -C test $@

#: Run py.test tests
pytest:
	$(MAKE) -C pytest check

#: Clean up temporary files and .pyc files
clean: clean_pyc
	$(PYTHON) ./setup.py $@
	(cd test && $(MAKE) clean)

#: Create source (tarball) and wheel distribution
dist:
	$(PYTHON) ./setup.py sdist bdist_wheel

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
bdist_wheel:
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
