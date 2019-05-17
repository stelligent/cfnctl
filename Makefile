export PIPENV_VENV_IN_PROJECT=1

default: all

deps:
	@echo "=== Dependencies ==="
	pipenv install

lint:
	pipenv run pylint cfnctl

build:
	@echo "=== Building ==="
	mkdir -p build
	mkdir -p dist
	rm -r ./build
	rm -r ./dist
	pipenv run python setup.py sdist bdist_wheel

install: build
	@echo "=== Installing ==="
	pip3 install --user ./

test:
	@echo "=== Testing ==="
	pipenv run python -m pytest test/unit --cov=cfnctl -W ignore::DeprecationWarning

coverage:
	@echo "=== Coverage ==="
	coverage run --source cfnctl -m unittest discover -v test "*.py"
	coverage report -m

deploy_test: lint test build
	@echo "=== Deploy test.pypi ==="
	@pipenv run twine upload dist/* -r testpypi
	# pip install --user -i https://test.pypi.org/simple/ cfnctl==0.3.3

deploy: lint test build
	@echo "=== Deploy pypi ==="
	@pipenv run twine upload dist/*

usage: install
	cfnctl --help

all: deps test build

.PHONY: default all lint build test coverage deploy_test usage
