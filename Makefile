all: flake8 pylint coverage
.PHONY: all

flake8:
	flake8 logsql tests
.PHONY: flake8

pylint:
	pylint logsql
	pylint tests --disable=missing-docstring,unused-argument
.PHONY: pylint

test:
	pytest -xv tests
.PHONY: test

test_pdb:
	pytest --pdb -xv tests
.PHONY: test_pdb

docs:
	sphinx-apidoc -f -o docs/source logsql
	make -C docs html
.PHONY: docs

coverage:
	pytest -xv --cov=logsql --cov-report=term-missing --cov-fail-under=100 tests/
.PHONY: coverage

wheel:
	python3 setup.py sdist bdist_wheel
.PHONY: wheel

pyenv:
	virtualenv -p python3 pyenv
	pyenv/bin/pip3 install -e .[prod]
.PHONY: pyenv

freeze:
	pyenv/bin/pip3 freeze | egrep -v -i "auth|flake8|pylint|pytest|docker-compose|pkg-resources|sphinx|logsql" > requirements.txt
.PHONY: freeze

clean:
	rm -rf build dist *.egg-info docs/build
	find . -name __pycache__ -prune -exec rm -rf '{}' ';'
.PHONY: clean