PHONY=check test pytest
SHELL=/bin/bash

PYTHON ?= python

#: Run all tests
test check pytest:
	@PYTHON_VERSION=`$(PYTHON) -V 2>&1 | cut -d ' ' -f 2 | cut -d'.' -f1,2`; \
	 if [[ $$PYTHON_VERSION > 3.2 ]] || [[ $$PYTHON_VERSION == 2.7 ]] || [[ $$PYTHON_VERSION == 2.6 ]]; then \
		py.test; \
	fi
