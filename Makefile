# Makefile for dx-without-excel project

.PHONY: test test-cov test-cov-html unit-test e2e-test clean install install-browsers lint format pre-commit help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies and setup pre-commit"
	@echo "  make install-browsers - Install Chromium browser for Playwright"
	@echo "  make test            - Run tests without coverage"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make test-cov-html   - Run tests with HTML coverage report and open it"
	@echo "  make unit-test       - Run unit tests only (no coverage)"
	@echo "  make run             - Run the Streamlit application"
	@echo "  make e2e-test-with-server - Run end-to-end tests with Streamlit server"
	@echo "  make e2e-test        - Run end-to-end tests only"
	@echo "  make fix-lint        - Fix linting issues with ruff"
	@echo "  make lint            - Run linting with ruff"
	@echo "  make format          - Format code with ruff"
	@echo "  make pre-commit      - Run pre-commit hooks manually"
	@echo "  make clean           - Clean generated files"

# Install dependencies
install:
	uv sync
	uv run pre-commit install
	uv run playwright install chromium

# Install Chromium browser for Playwright
install-browsers:
	uv run playwright install chromium

# Run tests without coverage
test:
	uv run pytest --no-cov

# Run tests with coverage (unit tests only)
test-cov:
	uv run pytest tests/unit/

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

# Run unit tests only
unit-test:
	uv run pytest tests/unit/ --no-cov

run:
	uv run streamlit run src/presentation/app.py

# Run end-to-end tests only
e2e-test:
	uv run pytest tests/e2e/ --no-cov

# Run end-to-end tests with Streamlit server
e2e-test-with-server:
	@echo "Starting Streamlit server..."
	@uv run streamlit run src/presentation/app.py --server.port 8501 --server.headless true &
	@SERVER_PID=$$!; \
	echo "Waiting for server to start..."; \
	sleep 5; \
	echo "Running E2E tests..."; \
	if uv run pytest tests/e2e/ --no-cov; then \
		echo "E2E tests passed"; \
		TEST_RESULT=0; \
	else \
		echo "E2E tests failed"; \
		TEST_RESULT=1; \
	fi; \
	echo "Stopping Streamlit server..."; \
	kill $$SERVER_PID 2>/dev/null || true; \
	exit $$TEST_RESULT

# Fix linting issues
fix-lint:
	uv run ruff check . --fix

# Run linting
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .
	uv run ruff check --fix .

# Run pre-commit hooks manually
pre-commit:
	uv run pre-commit run --all-files

# Clean generated files
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f coverage.xml
	rm -rf src/**/__pycache__
	rm -rf tests/**/__pycache__
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
