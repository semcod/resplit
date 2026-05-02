.PHONY: help install install-tui install-full test test-v lint fmt check coverage build clean publish \
        bump-patch bump-minor bump-major version tui walk-dry dashboard \
        docker-build docker-run

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
	@echo "  build          build wheel + sdist"
	@echo "  publish        upload to PyPI (requires TWINE_USERNAME/PASSWORD or trusted publishing)"
	@echo "  clean          remove build artifacts and __pycache__"
	@echo ""
	@echo "  version        show current version"
	@echo "  bump-patch     0.1.x → 0.1.(x+1)  + update CHANGELOG"
	@echo "  bump-minor     0.x.y → 0.(x+1).0   + update CHANGELOG"
	@echo "  bump-major     x.y.z → (x+1).0.0   + update CHANGELOG"
	@echo ""
	@echo "  coverage       run tests with coverage report (gate ≥70%)"
	@echo ""
	@echo "  docker-build   build Docker image locally"
	@echo "  docker-run     run rebuild CLI in Docker container"

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

coverage:
	python -m pytest --cov=rebuild --cov-report=term-missing --cov-report=xml -q
	@python - <<'EOF'
	import xml.etree.ElementTree as ET
	tree = ET.parse("coverage.xml")
	rate = float(tree.getroot().attrib.get("line-rate", 0)) * 100
	print(f"\nCoverage: {rate:.1f}%")
	if rate < 70:
	    raise SystemExit(f"Coverage {rate:.1f}% < 70% required")
	print("PASS: Coverage gate met ✓")
	EOF

version:
	@python3 scripts/bump_version.py --show

bump-patch:
	python3 scripts/bump_version.py patch

bump-minor:
	python3 scripts/bump_version.py minor

bump-major:
	python3 scripts/bump_version.py major

build: clean
	python3 -m build

publish: build
	python3 -m twine check dist/*
	python3 -m twine upload dist/*

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/

docker-build:
	docker build -t ghcr.io/semcod/rebuild:latest .

docker-run:
	docker run --rm -it \
	  -v $(PWD):/workspace \
	  -v /var/run/docker.sock:/var/run/docker.sock \
	  ghcr.io/semcod/rebuild:latest $(ARGS)
