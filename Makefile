.PHONY: help test

.DEFAULT: help

help:
	@echo "make test"
	@echo "    run tests"

test:
	PYTHONPATH=. poetry run pytest -vvv --cov=dataset --cov-report term-missing --cov-report=xml --disable-warnings
