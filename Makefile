# Makefile for dx-without-excel project

.PHONY: test test-cov test-cov-html e2e-test clean install install-browsers lint format help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies"
	@echo "  make install-browsers - Install Chromium browser for Playwright"
	@echo "  make test            - Run tests without coverage"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make test-cov-html   - Run tests with HTML coverage report and open it"
	@echo "  make e2e-test        - Run end-to-end tests only"
	@echo "  make lint            - Run linting with ruff"
	@echo "  make format          - Format code with ruff"
	@echo "  make clean           - Clean generated files"

# Install dependencies
install:
	uv sync

# Install Chromium browser for Playwright
install-browsers:
	uv run playwright install chromium

# Run tests without coverage
test:
	uv run pytest --no-cov

# Run tests with coverage
test-cov:
	uv run pytest

# Run tests with HTML coverage and open report
test-cov-html: test-cov
	@echo "Opening coverage report in browser..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open htmlcov/index.html; \
	elif command -v open > /dev/null; then \
		open htmlcov/index.html; \
	else \
		echo "Please open htmlcov/index.html in your browser"; \
	fi

# Run end-to-end tests only
e2e-test:
	uv run pytest tests/e2e/ --no-cov

# Run linting
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Clean generated files
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f coverage.xml
	rm -rf src/**/__pycache__
	rm -rf tests/**/__pycache__
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
