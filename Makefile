default: all

deps:
	@echo "=== Dependencies ==="
	python -m pip install --user --upgrade twine boto3==1.9.59

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

deploy_test: build
	@echo "=== Deploy test.pypi ==="
	@twine upload dist/* -r testpypi
	# pip install --user -i https://test.pypi.org/simple/ cfnctl==0.3.3

deploy: build
	@echo "=== Deploy pypi ==="
	@twine upload dist/*

usage: install
	cfnctl --help

all: deps test build

.PHONY: default all lint build test deploy_test usage 
