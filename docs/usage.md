# rebuild Usage Guide

This guide covers step-by-step usage of the Code Evolution Intelligence Engine.

## 1. Installation
```bash
pip install rebuild
playwright install chromium  # optional: for screenshots
```

## 2. Initialization
Bootstrap your project with a default configuration:
```bash
rebuild init
```
This generates:
- `rebuild.yaml`: Pipeline and deployment settings.
- `.env`: API keys for AI features (OpenRouter).

## 3. Historical Analysis (The Walk)

Analyze the last 30 days of git history:
```bash
rebuild walk . --days 30 --deploy auto
```

Common options:
```bash
# Without deployment (scan & test only)
rebuild walk . --days 30 --dry-run

# Custom health check timeout (useful for large stacks)
rebuild walk . --deploy docker-compose --health-timeout 300

# Custom health URL and base URL
rebuild walk . --health-url http://localhost:8080/health --base-url http://localhost:8080

# With manual patch overlay (apply fixes before each checkout)
rebuild walk . --patch-dir ./my-fixes/

# Serve results in browser after walk completes
rebuild walk . --serve --port 7821
```

### Deploy Modes

| Mode | Flag | Description |
|------|------|-------------|
| Auto-detect | `--deploy auto` | Detects docker-compose or uvicorn |
| Docker Compose | `--deploy docker-compose` | Full container build per commit |
| Replay | `--deploy docker-compose --replay` | Keeps containers alive, restarts per commit |
| No deploy | `--deploy none` | Only scans & tests against running service |
| Dry run | `--dry-run` | Scan endpoints only, no network calls |

### rebuild.yaml Configuration

```yaml
deploy:
  method: docker-compose
  health_url: http://localhost:8003/api/health
  health_timeout: 60          # increase for slow builds (e.g. 300)
  health_interval: 2

scan:
  days: 30

auth:
  login_url: http://localhost:8003/api/auth/login
  login_payload: {username: admin, password: secret}
  token_path: access_token    # JSON path in response

test_fixtures:
  id: 1
  slug: test-item

test_bodies:
  POST /api/items: {name: test, value: 42}
```

## 4. Code Intelligence (Queries)

### Duplication Detection
Find structural clones in Python and JS/TS:
```bash
rebuild analyze duplicates . --min-lines 5
```

### Architecture Graph
Export an interactive D3.js dependency map:
```bash
rebuild analyze services --export
```

### Truth Discovery
Find the most stable historical version of a function:
```bash
rebuild analyze truth path/to/file.py my_function
```

### Semantic Vector Search
```bash
rebuild analyze vector-build .        # build semantic index
rebuild analyze vector-query . "authentication handler"
```

## 5. Refactoring (Commands)

Generate a prioritized refactor plan with AI executive summary:
```bash
rebuild refactor plan . --ai
```

Automatically execute simple refactors:
```bash
rebuild refactor execute .
```

Generate a professional Pull Request description:
```bash
rebuild refactor pr .
```

Auto-create a PR on GitHub/GitLab:
```bash
rebuild auto-pr . --branch main --title "fix: endpoint regression"
```

## 6. Visualization

View the health timeline and quality metrics dashboard:
```bash
rebuild dashboard --repo .
```

Serve live results with SSE event streaming:
```bash
rebuild walk . --serve --port 7821
# or after a completed walk:
rebuild serve --output .rebuild --port 7821
```

Launch the interactive TUI:
```bash
rebuild tui
```

Code evolution playback (D3.js):
```bash
rebuild evolution --output .rebuild
```

## 7. Restore Working Endpoint

Extract the last working day's code for a broken endpoint:
```bash
rebuild restore /api/health . --output ./restored-health
```

## 8. DSL Scripting

Run a scripted sequence of rebuild operations:
```bash
rebuild dsl run my-script.dsl
```

Example `.dsl` file:
```
walk repo:/path/to/repo days:7 deploy:docker-compose
analyze duplicates repo:/path/to/repo
restore endpoint:/api/health repo:/path/to/repo
```

## 9. Accelerator Mode (10x faster)

Reuses node_modules and bind-mounts code — no full rebuild:
```bash
rebuild accelerator . --service backend --parallel 4 --smart
```

## 10. Error Diagnosis

When deploy fails, rebuild classifies the error automatically:

| Category | Description |
|----------|-------------|
| `compose_build_fail` | Dockerfile build error (npm, pip, etc.) |
| `port_conflict` | Port already in use |
| `migration_fail` | DB migration error |
| `missing_env` | Missing environment variable |
| `unknown` | Unclassified failure |

Full deploy logs are saved in `.rebuild/YYYY-MM-DD/results.json` under `deploy.log`.
