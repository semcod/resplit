# rebuild


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.9-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.35-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-2.5h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $1.3500 (9 commits)
- 👤 **Human dev:** ~$248 (2.5h @ $100/h, 30min dedup)

Generated on 2026-05-01 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

**Historical deployment analysis** — walk git history day by day, deploy per commit, test all endpoints, capture screenshots, restore working fragments.

![Version](https://img.shields.io/badge/version-0.1.9-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Tests](https://img.shields.io/badge/tests-44%20passing-brightgreen)

---

## What it does

1. **Walk** — iterates through git history day by day (configurable range)
2. **Deploy** — starts the service per commit (docker-compose / uvicorn / none)
3. **Scan** — `deta` (service-level) → OpenAPI (API-level) → Traefik labels fallback
4. **Test** — `testql` scenarios (detailed API) or HTTP probe fallback (service-level)
5. **Screenshot** — Playwright screenshots per endpoint with retry/timeout
6. **Report** — generates `report.html` + `results.json` per day + timeline `index.html`
7. **Restore** — extracts the last working day of an endpoint as an isolated Docker project
8. **Dashboard** — overlays health% timeline with avg cyclomatic complexity (via `toon`)
9. **TUI** — interactive terminal menu: project → walk → history → diff → restore

---

## Install

```bash
pip install rebuild

# with interactive TUI
pip install "rebuild[tui]"

# with Playwright screenshots
pip install "rebuild[screenshots]"
playwright install chromium

# everything
pip install "rebuild[full]"
playwright install chromium

# development
pip install -e ".[dev]"
```

---

## Quick start

```bash
# Interactive TUI (recommended)
rebuild tui

# Dry-run: scan last 30 days without deploy
rebuild walk . --days 30 --dry-run

# Full walk with docker-compose
rebuild walk . --days 30 --deploy docker-compose

# Walk a specific date range
rebuild walk /path/to/repo --from 2024-01-01 --to 2024-04-01

# Restore last working version of an endpoint
rebuild restore /api/health .

# Generate timeline report from existing results
rebuild report

# Generate CC vs health% dashboard
rebuild dashboard --repo .

# Show version
rebuild version
```

---

## CLI reference

### `rebuild walk`

```
rebuild walk [REPO] [OPTIONS]

  REPO                    Path to git repository (default: .)

Options:
  --days INT              How many days back (default: 30)
  --from TEXT             Start date YYYY-MM-DD
  --to TEXT               End date YYYY-MM-DD
  --output PATH           Output directory (default: .rebuild)
  --deploy TEXT           Deploy method: auto|docker-compose|uvicorn|none
  --health-url TEXT       Health check URL (default: http://localhost:8003/api/health)
  --base-url TEXT         Base service URL (default: http://localhost:8003)
  --screenshots / --no-screenshots
                          Take Playwright screenshots (default: true)
  --dry-run               Scan only, no deploy
```

### `rebuild restore`

```
rebuild restore ENDPOINT [REPO] [OPTIONS]

  ENDPOINT                Endpoint path e.g. /api/health

Options:
  --output PATH           Target project directory (default: restored/)
  --results-dir PATH      Walk results directory (default: .rebuild)
```

### `rebuild report`

```
rebuild report [OPTIONS]

Options:
  --results-dir PATH      Walk results directory (default: .rebuild)
```

### `rebuild dashboard`

```
rebuild dashboard [OPTIONS]

Options:
  --results-dir PATH      Walk results directory (default: .rebuild)
  --repo PATH             Repository path for CC extraction via toon (optional)
```

### `rebuild tui`

```
rebuild tui
```

Interactive terminal UI — requires `pip install "rebuild[tui]"`. No options needed.

**TUI flow:**
```
ProjectScreen
  ├── [Open history]  → HistoryScreen
  │                       ├── [Diff]      → EndpointDetailScreen (diff mode)
  │                       ├── [Endpoints] → EndpointDetailScreen (detail mode)
  │                       └── [Restore]   → RestoreScreen → docker compose up -d
  └── [New walk]      → WalkConfigScreen → WalkProgressScreen → HistoryScreen
```

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `D` | Diff vs previous day |
| `R` | Restore selected endpoint |
| `Enter` | Endpoint details for selected day |
| `F1` | Help |
| `Escape` | Back |
| `Ctrl+C` | Quit |

---

## Output structure

```
.rebuild/
  2024-03-15/
    commit.txt              # sha · message · author · timestamp
    endpoints.json          # detected endpoints
    results.json            # HTTP / testql results per endpoint
    testql-results.json     # raw testql output (if testql available)
    report.html             # per-day HTML report with screenshots
    screenshots/
      GET_api_health.png
      GET_api_items.png
  index.html                # timeline of all days
  dashboard.html            # CC vs health% chart (after rebuild dashboard)
```

---

## Configuration — `rebuild.yaml`

```yaml
project:
  name: "my-api"
  repo: "."

deploy:
  method: docker-compose          # docker-compose | uvicorn | custom | none
  compose_file: docker-compose.yml
  health_url: http://localhost:8003/api/health
  health_timeout: 60
  health_interval: 2

scan:
  days: 30
  earliest_commit_per_day: true

testql:
  scenarios_dir: testql-scenarios/
  base_url: http://localhost:8003
  timeout: 10

output:
  dir: .rebuild
  screenshots: true
  html_report: true
```

---

## Architecture

```
rebuild/
├── rebuild/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI: walk, restore, report, version, dashboard, tui
│   ├── models.py           # Dataclasses: WalkConfig, DayResult, Endpoint, CommitInfo
│   ├── git_walker.py       # Day-by-day git history iteration
│   ├── deployer.py         # Deploy method detection + docker-compose/uvicorn lifecycle
│   ├── endpoint_scanner.py # deta (service) → OpenAPI (API) → Traefik labels fallback
│   ├── tester.py           # testql scenarios (API-level) + HTTP probe fallback
│   ├── screenshotter.py    # Playwright screenshots with retry/timeout
│   ├── reporter.py         # HTML + JSON report per day + timeline index
│   ├── restorer.py         # Extract last working endpoint as isolated Docker project
│   ├── dashboard.py        # CC (toon) vs health% comparative timeline
│   └── tui.py              # Textual TUI — 6-screen interactive menu
├── tests/                  # 44 tests (pytest)
├── examples/
│   ├── 01-dry-run-walk/
│   ├── 02-docker-compose-project/
│   └── 03-restore-endpoint/
├── testql-scenarios/
├── pyproject.toml
└── rebuild.yaml.example
```

### Endpoint scanner — 3-level fallback

| Level | Source | What it returns |
|-------|--------|-----------------|
| 1 | `deta scan` | services → ports → health paths |
| 2 | `/openapi.json` | full endpoint list from OpenAPI spec |
| 3 | docker-compose Traefik labels | `PathPrefix` rules |
| 4 | hardcoded fallback | `GET /api/health` |

### Tester — 2-level fallback

| Level | Condition | Behaviour |
|-------|-----------|-----------|
| 1 | `testql` installed + `testql_dir` set | runs `.testql.yaml` scenarios |
| 2 | fallback | HTTP GET probe per endpoint |

---

## Module summary

| Module | CC̄ | Functions | Purpose |
|--------|-----|-----------|---------|
| `cli` | 6.3 | 9 | CLI entry points (incl. `tui`) |
| `models` | — | — | Dataclasses only |
| `git_walker` | 3.3 | 6 | Git history iteration |
| `deployer` | 3.5 | 9 | Deploy lifecycle |
| `endpoint_scanner` | 5.5 | 6 | Endpoint detection (deta+OpenAPI+Traefik) |
| `tester` | 4.3 | 6 | testql (API-level) + HTTP probe (service-level) |
| `screenshotter` | 3.6 | 5 | Playwright screenshots with retry |
| `reporter` | 6.0 | 6 | HTML/JSON reports |
| `restorer` | 5.5 | 5 | Endpoint extraction → isolated Docker project |
| `dashboard` | 4.5 | 4 | CC vs health% chart |
| `tui` | — | 6 screens | Interactive Textual TUI |

> **Hotspots** (CC ≥ 9): `walk` (CC=15), `report` (CC=13), `extract_endpoint` (CC=9), `save_html` (CC=9), `_scan_via_compose_labels` (CC=9)

---

## Dependencies

**Runtime:** `typer>=0.12`, `rich>=13`, `gitpython>=3.1`, `httpx>=0.27`, `pyyaml>=6`, `pydantic>=2`, `deta>=0.1`

**Optional:** `playwright>=1.44` (screenshots)

**Dev:** `pytest>=8`, `pytest-cov`, `pytest-asyncio`, `ruff`, `mypy`

---

## Examples

See [`examples/`](examples/) for ready-to-run scenarios:

- [`01-dry-run-walk/`](examples/01-dry-run-walk/) — scan history without deploy
- [`02-docker-compose-project/`](examples/02-docker-compose-project/) — full walk with docker + screenshots + dashboard
- [`03-restore-endpoint/`](examples/03-restore-endpoint/) — restore last working endpoint as isolated project

---

## License

Licensed under Apache-2.0.
