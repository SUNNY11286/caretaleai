.PHONY: help install build test clean lint format test-pbt test-pbt-intensive

help:
	@echo "CARETALE AI - Development Commands"
	@echo ""
	@echo "install          - Install all dependencies (TypeScript and Python)"
	@echo "build            - Build TypeScript project"
	@echo "test             - Run all tests (TypeScript and Python)"
	@echo "test-ts          - Run TypeScript tests only"
	@echo "test-py          - Run Python tests only"
	@echo "test-pbt         - Run property-based tests with standard profile (100 iterations)"
	@echo "test-pbt-intensive - Run property-based tests with intensive profile (500 iterations)"
	@echo "lint             - Run linters for both TypeScript and Python"
	@echo "format           - Format code for both TypeScript and Python"
	@echo "clean            - Remove build artifacts and caches"

install:
	npm install
	pip install -r requirements.txt

build:
	npm run build

test: test-ts test-py

test-ts:
	npm test

test-py:
	pytest

test-pbt:
	@echo "Running property-based tests with standard profile (100 iterations)..."
	pytest --hypothesis-profile=standard -v -k "property"
	npm test -- --testNamePattern="Property"

test-pbt-intensive:
	@echo "Running property-based tests with intensive profile (500 iterations)..."
	pytest --hypothesis-profile=intensive -v -k "property"
	npm test -- --testNamePattern="Property"

lint:
	npm run lint
	ruff python/
	mypy python/src

format:
	npm run format
	black python/

clean:
	rm -rf dist/
	rm -rf node_modules/
	rm -rf coverage/
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .hypothesis/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
