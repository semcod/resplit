.PHONY: help install install-tui install-full test test-v lint fmt check build clean tui walk-dry dashboard

help:
	@echo "rebuild — available targets:"
	@echo ""
	@echo "  install        pip install -e .[dev]"
	@echo "  install-tui    pip install -e .[dev,tui]"
	@echo "  install-full   pip install -e .[dev,tui,screenshots]"
	@echo ""
	@echo "  test           run all tests (pytest -q)"
	@echo "  test-v         run tests verbose"
	@echo "  lint           ruff check"
	@echo "  fmt            ruff format"
	@echo "  check          lint + test"
	@echo ""
	@echo "  tui            launch interactive TUI"
	@echo "  walk-dry       dry-run walk on current repo"
	@echo "  dashboard      generate CC vs health% dashboard"
	@echo ""
	@echo "  build          build distribution packages"
	@echo "  clean          remove build artifacts and __pycache__"

install:
	pip install -e ".[dev]"

install-tui:
	pip install -e ".[dev,tui]"

install-full:
	pip install -e ".[dev,tui,screenshots]"
	playwright install chromium

test:
	python -m pytest tests/ -q

test-v:
	python -m pytest tests/ -v

lint:
	ruff check rebuild/ tests/

fmt:
	ruff format rebuild/ tests/

check: lint test

tui:
	rebuild tui

walk-dry:
	rebuild walk . --days 30 --dry-run --no-screenshots

dashboard:
	rebuild dashboard --repo .

build:
	python -m build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/
