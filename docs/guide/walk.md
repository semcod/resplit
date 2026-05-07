# Walk Command

> See also: [CLI Reference](../reference/cli.md#rebuild-walk) · [Configuration](../getting-started/configuration.md) · [Usage Guide](../usage.md#3-historical-analysis-the-walk)

The `walk` command is the core of `rebuild`. It iterates your git history, deploys each commit (or tests against an already-running stack), discovers and exercises every API endpoint, and produces a rich HTML timeline.

## Basic usage

```bash
rebuild walk /path/to/repo --deploy none --days 14
```

## Deploy modes

| Mode | When to use |
|---|---|
| `none` | Stack is already running; just test endpoints against it |
| `docker-compose` | Rebuild and redeploy from scratch per commit |
| `auto` | Auto-detect based on presence of `docker-compose.yml` |
| `custom` | Run `deploy.sh` in repo root |

## Dry run

```bash
rebuild walk . --dry-run --days 7
```

Dry-run mode skips all deployment and only walks history + reports what it would do.

## Output structure

```
.rebuild/
  index.html          ← Timeline dashboard
  dashboard.html      ← Health % vs CC chart
  summary.csv         ← Machine-readable summary
  summary.md          ← Markdown summary
  2025-01-01/
    report.html
    results.json
    screenshots/
  2025-01-02/
    ...
```

## Using rebuild.yaml

Place a `rebuild.yaml` in your repo root to avoid repeating flags:

```yaml
project:
  days: 30
  deploy:
    method: none
    health_url: http://localhost:8000/health
    health_timeout: 120
  base_url: http://localhost:8000
```

CLI flags always override `rebuild.yaml` values. See [Configuration reference](../reference/config.md) for all fields.
