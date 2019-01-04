default: all

deps:
	@echo "=== Dependencies ==="
	python -m pip install --user --upgrade twine boto3==1.9.59 coverage

lint:
	pylint cfnctl

build:
	@echo "=== Building ==="
	rm -r ./build
	rm -r ./dist
	@./setup.py sdist bdist_wheel

install: build
	@echo "=== Installing ==="
	pip install --user ./

test:
	@echo "=== Testing ==="
	python -m unittest discover -v test "*.py"

coverage:
	@echo "=== Coverage ==="
	coverage run --source cfnctl -m unittest discover -v test "*.py"
	coverage report -m

deploy_test: lint test build
	@echo "=== Deploy test.pypi ==="
	@twine upload dist/* -r testpypi
	# pip install --user -i https://test.pypi.org/simple/ cfnctl==0.3.3

deploy: lint test build
	@echo "=== Deploy pypi ==="
	@twine upload dist/*

usage: install
	cfnctl --help

all: deps test build

.PHONY: default all lint build test coverage deploy_test usage 
