# rebuild


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.11-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.65-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.7h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $1.6500 (11 commits)
- 👤 **Human dev:** ~$366 (3.7h @ $100/h, 30min dedup)

Generated on 2026-05-01 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---



## Code Evolution Intelligence Engine

![Version](https://img.shields.io/badge/version-0.1.11-blue) ![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green) ![Tests](https://img.shields.io/badge/tests-65%20passing-brightgreen)

**Historical deployment analysis & Code Intelligence** — walk git history day by day, deploy per commit, test all endpoints, capture screenshots, and **analyze code evolution** to find duplicates, rank quality, and generate refactor plans.

---

## 📖 Documentation
- **[Full Usage Guide](docs/usage.md)**: Step-by-step instructions.
- **[Architecture](docs/architecture.md)**: Detailed layered design.
- **[Changelog](CHANGELOG.md)**: Latest v0.1.10 features.

---

## What it does

1. **Intelligence Layer** — Detects structural duplicates (Python/JS/TS), builds service graphs, and ranks code quality across history.
2. **Decision Engine** — Generates and executes refactoring plans with **AI support**.
3. **Walk** — Iterates through git history day by day (Incremental support).
4. **Deploy** — Starts the service per commit (Isolated Docker environments).
5. **Scan & Test** — Automated endpoint discovery and TestQL execution.
6. **Visualization** — D3.js interactive graphs and health dashboards.

---

## Quick start

### 🚀 Bootstrapping

```bash
# Initialize project config and .env
rebuild init
```

### 🧠 Intelligence & Analysis

```bash
# Find duplicates across Python and JS/TS
rebuild analyze duplicates .

# Export interactive architecture graph
rebuild analyze services --export

# Generate AI-powered refactor plan and PR description
rebuild refactor plan . --ai
rebuild refactor pr .
```

### 🏃 Execution Pipeline

```bash
# Analyze last 30 days history (Incremental)
rebuild walk . --days 30

# Launch TUI
rebuild tui
```

---

## Examples

Explore ready-to-run scenarios in [`examples/`](examples/):

- **[01-dry-run-walk](examples/01-dry-run-walk/)**: Standard walk + intelligence.
- **[02-docker-compose-project](examples/02-docker-compose-project/)**: Full pipeline with **Docker isolation**.
- **[03-restore-endpoint](examples/03-restore-endpoint/)**: Discovering "truth" and extracting endpoints.

---

## License

Licensed under Apache-2.0.
