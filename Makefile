SPHINXBUILD ?= .venv/bin/sphinx-build
PY          ?= .venv/bin/python

.PHONY: html lint check clean
html:
	$(SPHINXBUILD) -W --keep-going -b html . _build/html
lint:
	$(PY) tools/lint_rst.py
check: lint html
clean:
	rm -rf _build
