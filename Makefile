.PHONY: help install install-dev test test-cov lint format type-check check build publish clean

PYTHON   ?= python
PIP      ?= pip
SRC      := ai_guardian
TESTS    := tests

# Default target
help:
	@echo "ai-guardian — development commands"
	@echo ""
	@echo "  make install       Install the package (core only)"
	@echo "  make install-dev   Install all dev dependencies (editable)"
	@echo "  make test          Run the test suite"
	@echo "  make test-cov      Run tests with HTML coverage report"
	@echo "  make lint          ruff lint check"
	@echo "  make format        ruff auto-format"
	@echo "  make type-check    mypy strict check"
	@echo "  make check         lint + format-check + type-check (CI equivalent)"
	@echo "  make build         Build wheel and sdist"
	@echo "  make publish       Publish to PyPI (requires twine + credentials)"
	@echo "  make clean         Remove build / cache artifacts"

# ── Setup ─────────────────────────────────────────────────────────────────────

install:
	$(PIP) install .

install-dev:
	$(PIP) install -e '.[dev]'

# ── Testing ──────────────────────────────────────────────────────────────────

test:
	pytest $(TESTS)/ -v

test-cov:
	pytest $(TESTS)/ -v \
		--cov=$(SRC) \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml
	@echo "\nCoverage report: htmlcov/index.html"

# ── Linting & formatting ───────────────────────────────────────────────────────

lint:
	ruff check $(SRC)/ $(TESTS)/

format:
	ruff format $(SRC)/ $(TESTS)/

format-check:
	ruff format --check $(SRC)/ $(TESTS)/

type-check:
	mypy $(SRC)/

check: lint format-check type-check
	@echo "\nAll checks passed."

# ── Build & publish ───────────────────────────────────────────────────────────

build: clean
	$(PYTHON) -m build
	twine check dist/*

publish: build
	twine upload dist/*

publish-test: build
	twine upload --repository testpypi dist/*

# ── Housekeeping ─────────────────────────────────────────────────────────────

clean:
	rm -rf dist/ build/ *.egg-info .eggs/
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache  -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache  -exec rm -rf {} + 2>/dev/null || true
