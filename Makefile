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
PHONY=check clean dist distclean test test-unit test-functional rmChangeLog clean_pyc nosetests

#: Default target - same as "check"
all: check

#: Make HTML docs
html:
	cd docs && $(MAKE) html

#: Same as "check"
test: check

#: Same as "check"
nosetests: check

#: Run all tests
check-short: test-unit-short

#: Run all tests: unit, functional and integration verbosely
check: test-unit lint

#: Run unit (white-box) tests
test-unit:
	$(PYTHON) ./setup.py nosetests

#: Run unit (white-box) tests
test-unit-short:
	$(PYTHON) ./setup.py nosetests --quiet 2>&1 | \
	$(PYTHON) ./test/make-check-filter.py

#: Clean up temporary files and .pyc files
clean: clean_pyc
	$(PYTHON) ./setup.py $@

#: Create source (tarball) and binary (egg) distribution
dist:
	$(PYTHON) ./setup.py sdist bdist_egg

#: Remove .pyc files
clean_pyc:
	$(RM) -f */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc

#: Create source tarball
sdist:
	$(PYTHON) ./setup.py sdist


#: Style check. Set env var LINT to pyflakes, flake, or flake8
lint:
	$(LINT) trepan_deparse/deparser.py

#: Create binary egg distribution
bdist_egg:
	$(PYTHON) ./setup.py bdist_egg


# It is too much work to figure out how to add a new command to distutils
# to do the following. I'm sure distutils will someday get there.
DISTCLEAN_FILES = build dist *.pyc

#: Remove ALL derived files
distclean: clean
	-rm -fr $(DISTCLEAN_FILES) || true
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
