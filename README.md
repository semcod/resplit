# rebuild


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.10-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.50-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-2.5h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $1.5000 (10 commits)
- 👤 **Human dev:** ~$249 (2.5h @ $100/h, 30min dedup)

Generated on 2026-05-01 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## Code Evolution Intelligence Engine

![Version](https://img.shields.io/badge/version-0.1.10-blue) ![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green) ![Tests](https://img.shields.io/badge/tests-65%20passing-brightgreen)

**Historical deployment analysis & Code Intelligence** — walk git history day by day, deploy per commit, test all endpoints, capture screenshots, and **analyze code evolution** to find duplicates, rank quality, and generate refactor plans.

---

## What it does

1. **Intelligence Layer (NEW)** — Detects structural duplicates, builds service graphs, and ranks code quality across history.
2. **Decision Engine (NEW)** — Generates actionable refactoring plans (Merge/Extract/Split) with clear rationale.
3. **Walk** — Iterates through git history day by day (earliest commit per day).
4. **Deploy** — Starts the service per commit: docker-compose / uvicorn / none.
5. **Scan** — `deta` (service-level) → OpenAPI (API-level) → Traefik labels fallback.
6. **Test** — `testql` scenarios (detailed API) or HTTP probe fallback (service-level).
7. **Screenshot** — Playwright screenshots per endpoint with retry/timeout.
8. **Restore** — Extract last working endpoint as isolated Docker project.
9. **Dashboard** — Health% timeline overlaid with quality metrics.
10. **TUI** — Interactive terminal menu for project exploration and recovery.

---

## Install

```bash
pip install rebuild

# with full intelligence suite (recommended)
pip install "rebuild[full]"
playwright install chromium
```

---

## Quick start

### 🚀 Analysis & Intelligence (New in v0.1.10)

```bash
# Find structural and semantic duplicates
rebuild analyze duplicates .

# Visualize service architecture graph and detect cycles
rebuild analyze services

# Find the 'best' historical version of a function
rebuild analyze truth rebuild/application/pipeline.py run_day

# Generate a prioritized refactoring plan
rebuild refactor plan .
```

### 🏃 Execution Pipeline

```bash
# Interactive TUI
rebuild tui

# Dry-run walk: scan last 30 days without deploy
rebuild walk . --days 30 --dry-run

# Restore last working version of an endpoint
rebuild restore /api/health .

# Generate health vs quality dashboard
rebuild dashboard --repo .
```

---

## Examples

Explore ready-to-run scenarios in [`examples/`](examples/):

- **[01-dry-run-walk](examples/01-dry-run-walk/)**: Standard walk without deployment + intelligence analysis.
- **[02-docker-compose-project](examples/02-docker-compose-project/)**: Full pipeline with **Docker isolation**, screenshots, and architectural refactor plan.
- **[03-restore-endpoint](examples/03-restore-endpoint/)**: Discovering historical "truth" and extracting a working endpoint as a standalone project.

To run any example:
```bash
cd examples/01-dry-run-walk
./run.sh ../.. 30
```

---

## Architecture

Rebuild follows a strict layered architecture:
`Interfaces → Application (Pipeline/Services) → Intelligence (Analysis/Refactor) → Domain → Infrastructure`.

Detailed documentation: [docs/architecture.md](docs/architecture.md)

```
rebuild/
├── analysis/           # Intelligence layer: duplication, truth ranking, service graph
├── application/        # Application logic: Pipeline and injected Services
├── domain/             # Pure data models (Endpoint, DayResult, CommitInfo)
├── infrastructure/     # External adapters (Git, HTTP, Playwright)
├── interfaces/         # Entrypoints: CLI, TUI, Dashboard
└── refactor/           # Decision engine: Refactor recommendation engine
```

---

## Changelog & Roadmap

- See [CHANGELOG.md](CHANGELOG.md) for the latest updates.
- See [TODO.md](TODO.md) for the future roadmap (Automated Refactoring, LLM assistance).

---

## License

Licensed under Apache-2.0.
