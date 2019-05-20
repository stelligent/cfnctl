export PIPENV_VENV_IN_PROJECT=1
export AWS_DEFAULT_REGION=us-east-1

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
	pipenv run pip install ./

test:
	@echo "=== Testing ==="
	pipenv run python -m pytest test/unit --cov=cfnctl -W ignore::DeprecationWarning

deploy_test: lint test build
	@echo "=== Deploy test.pypi ==="
	@pipenv run twine upload dist/* -r testpypi
	# pip install --user -i https://test.pypi.org/simple/ cfnctl==0.3.3

deploy: lint test build
	@echo "=== Deploy pypi ==="
	@pipenv run twine upload dist/*

usage: install
	pipenv run cfnctl --help

all: deps lint test build

.PHONY: default all lint build test deploy_test usage
