SHELL := /usr/bin/env bash
TEAMS_PATH := ./teams
PYTHON_BIN := /usr/bin/env python
ALL_CHANGED_FILES ?= test

.PHONY: setup
setup: setup_python setup_npm

.PHONY: setup_python
setup:
	pip install -r requirements.txt

.PHONY: setup_npm
setup_npm:
	npm install

.PHONY: test
test: test_yaml test_prettier

.PHONY: test_yaml
test_yaml:
	$(PYTHON_BIN) -m yamllint --version && \
	$(PYTHON_BIN) -m yamllint $(TEAMS_PATH)

.PHONY: test_prettier
test_prettier:
	npx prettier --version && \
	npx prettier --check .

.PHONY: test_changes
test_changes:
	$(PYTHON_BIN) .github/src/change_verify.py $(ALL_CHANGED_FILES)
