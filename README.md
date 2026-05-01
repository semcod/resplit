# resplit


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.5-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.75-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-2.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.7500 (5 commits)
- 👤 **Human dev:** ~$201 (2.0h @ $100/h, 30min dedup)

Generated on 2026-05-01 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

**Historical deployment analysis** — walk git history day by day, deploy per commit, test all endpoints, capture screenshots, restore working fragments.

![Version](https://img.shields.io/badge/version-0.1.5-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Tests](https://img.shields.io/badge/tests-44%20passing-brightgreen)

---

## What it does

1. **Walk** — iterates through git history day by day (configurable range)
2. **Deploy** — starts the service per commit (docker-compose / uvicorn / none)
3. **Scan** — detects endpoints via `deta scan` → OpenAPI → Traefik labels fallback
4. **Test** — runs `testql` scenarios or falls back to HTTP probe per endpoint
5. **Screenshot** — Playwright screenshots per endpoint with retry/timeout
6. **Report** — generates `report.html` + `results.json` per day + timeline `index.html`
7. **Restore** — extracts the last working day of an endpoint as an isolated project
8. **Dashboard** — overlays health% timeline with avg cyclomatic complexity (via `toon`)

---

## Install

```bash
pip install resplit

# with Playwright screenshots
pip install "resplit[screenshots]"
playwright install chromium

# development
pip install -e ".[dev]"
```

---

## Quick start

```bash
# Dry-run: scan last 30 days without deploy
resplit walk . --days 30 --dry-run

# Full walk with docker-compose
resplit walk . --days 30 --deploy docker-compose

# Walk a specific date range
resplit walk /path/to/repo --from 2024-01-01 --to 2024-04-01

# Restore last working version of an endpoint
resplit restore /api/health .

# Generate timeline report from existing results
resplit report

# Generate CC vs health% dashboard
resplit dashboard --repo .

# Show version
resplit version
```

---

## CLI reference

### `resplit walk`

```
resplit walk [REPO] [OPTIONS]

  REPO                    Path to git repository (default: .)

Options:
  --days INT              How many days back (default: 30)
  --from TEXT             Start date YYYY-MM-DD
  --to TEXT               End date YYYY-MM-DD
  --output PATH           Output directory (default: .resplit)
  --deploy TEXT           Deploy method: auto|docker-compose|uvicorn|none
  --health-url TEXT       Health check URL (default: http://localhost:8003/api/health)
  --base-url TEXT         Base service URL (default: http://localhost:8003)
  --screenshots / --no-screenshots
                          Take Playwright screenshots (default: true)
  --dry-run               Scan only, no deploy
```

### `resplit restore`

```
resplit restore ENDPOINT [REPO] [OPTIONS]

  ENDPOINT                Endpoint path e.g. /api/health

Options:
  --output PATH           Target project directory (default: restored/)
  --results-dir PATH      Walk results directory (default: .resplit)
```

### `resplit report`

```
resplit report [OPTIONS]

Options:
  --results-dir PATH      Walk results directory (default: .resplit)
```

### `resplit dashboard`

```
resplit dashboard [OPTIONS]

Options:
  --results-dir PATH      Walk results directory (default: .resplit)
  --repo PATH             Repository path for CC extraction via toon (optional)
```

---

## Output structure

```
.resplit/
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
  dashboard.html            # CC vs health% chart (after resplit dashboard)
```

---

## Configuration — `resplit.yaml`

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
  dir: .resplit
  screenshots: true
  html_report: true
```

---

## Architecture

```
resplit/
├── resplit/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI: walk, restore, report, version, dashboard
│   ├── models.py           # Dataclasses: WalkConfig, DayResult, Endpoint, CommitInfo
│   ├── git_walker.py       # Day-by-day git history iteration
│   ├── deployer.py         # Deploy method detection + docker-compose/uvicorn lifecycle
│   ├── endpoint_scanner.py # deta scan → OpenAPI → Traefik labels fallback
│   ├── tester.py           # testql runner with HTTP probe fallback
│   ├── screenshotter.py    # Playwright screenshots with retry/timeout
│   ├── reporter.py         # HTML + JSON report per day + timeline index
│   ├── restorer.py         # Extract last working endpoint as isolated project
│   └── dashboard.py        # CC (toon) vs health% comparative timeline
├── tests/                  # 44 tests (pytest)
├── examples/
│   ├── 01-dry-run-walk/
│   ├── 02-docker-compose-project/
│   └── 03-restore-endpoint/
├── testql-scenarios/
├── pyproject.toml
└── resplit.yaml.example
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
| `cli` | 6.3 | 8 | CLI entry points |
| `models` | — | — | Dataclasses only |
| `git_walker` | 3.3 | 6 | Git history iteration |
| `deployer` | 3.5 | 9 | Deploy lifecycle |
| `endpoint_scanner` | 5.5 | 6 | Endpoint detection |
| `tester` | 4.3 | 6 | Endpoint testing |
| `screenshotter` | 3.6 | 5 | Screenshots |
| `reporter` | 6.0 | 6 | HTML/JSON reports |
| `restorer` | 5.5 | 5 | Endpoint extraction |
| `dashboard` | 4.5 | 4 | CC vs health chart |

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
