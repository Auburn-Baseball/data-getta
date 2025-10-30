.PHONY: help process test coverage clean install lint format check type-check

PYTHON = poetry run python3
PYTEST = poetry run pytest
BLACK = poetry run black
ISORT = poetry run isort
FLAKE8 = poetry run flake8
MYPY = poetry run mypy --config-file=pyproject.toml

help:
	@echo "Available commands:"
	@echo "  make process       - Run data processing"
	@echo "  make process-args  - Run data processing with arguments (${argv})"
	@echo "  make test          - Run tests"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo "  make coverage      - Run tests with coverage"
	@echo "  make lint          - Run all linters"
	@echo "  make format        - Auto-format code"
	@echo "  make format-check  - Check if formatting is needed"
	@echo "  make type-check    - Run type checker"
	@echo "  make check         - Run all checks (lint + type + test)"
	@echo "  make clean         - Remove cache files"
	@echo "  make install       - Install dependencies"

# Main commands
process:
	$(PYTHON) process_all_data.py

process-args:
	$(PYTHON) process_all_data.py $(ARGS)

qa:
	$(PYTHON) QA/process_local_csv.py

# Testing
test:
	$(PYTEST)

test-watch:
	poetry run ptw

test-fast:
	$(PYTEST) -x  # Stop on first failure

coverage:
	$(PYTEST) --cov --cov-report=html
	@echo "\nCoverage report: htmlcov/index.html"

# Formatting
format:
	@echo "Sorting imports..."
	$(ISORT) utils/ tests/ *.py
	@echo "Formatting code..."
	$(BLACK) utils/ tests/ *.py
	@echo "Formatting complete!"

format-check:
	@echo "Checking code formatting..."
	$(BLACK) --check utils/ tests/ *.py
	$(ISORT) --check-only utils/ tests/ *.py

# Linting
lint:
	@echo "Running flake8..."
	$(FLAKE8) utils/ *.py
	@echo "Linting complete!"

type-check:
	@echo "Running mypy..."
	cd .. && poetry -C scripts run pre-commit run mypy --all-files
	@echo "Type checking complete!"

# Run all checks
check: format lint type-check test
	@echo "\nAll checks passed!"

# Pre-commit hook (run before committing)
pre-commit: format lint type-check test-fast
	cd .. && poetry run pre-commit run --all-files
	@echo "\nReady to commit!"

# Installation
install:
	poetry install

install-dev:
	poetry install --with dev

update:
	poetry update

# Cleaning
clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	@echo "Clean complete!"

# Show current environment info
info:
	@echo "Python version:"
	@$(PYTHON) --version
	@echo "\nPoetry version:"
	@poetry --version
	@echo "\nInstalled packages:"
	@poetry show --tree

# Specific table processing (if you refactor to have main() functions)
process-pitchers:
	$(PYTHON) -c "from utils.update_pitchers_table import main; main()"

process-batters:
	$(PYTHON) -c "from utils.update_batters_table import main; main()"
