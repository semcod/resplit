# rebuild

**Code Evolution Intelligence Engine** — walk git history day by day, deploy each commit, test all endpoints, capture screenshots, and **analyze code evolution** to find duplicates, rank quality, and generate refactor plans.

> **v0.1.23** · 634 tests · 72% coverage · 3722 functions · 161 classes · CC̄ = 3.9

---

## What is rebuild?

`rebuild` answers the question: *"When exactly did this service break — and what was the last known-good commit?"*

It walks your git history, deploys each commit (or uses an already-running stack), exercises every discovered API endpoint, captures screenshots, and produces a rich HTML timeline showing health trends over time.

```
git history  →  deploy  →  test endpoints  →  capture screenshots  →  report
```

---

## Key Features

| Feature | Description | Docs |
|---|---|---|
| **Walk** | Iterate git history, deploy per commit, test all endpoints | [Guide](guide/walk.md) · [CLI](reference/cli.md#rebuild-walk) |
| **Analyze** | Detect code duplication, service graph cycles, semantic similarity | [Guide](guide/analyze.md) |
| **Refactor** | AI-powered refactoring plans + automated execution | [Guide](guide/refactor.md) |
| **Auto-PR** | Open GitHub/GitLab PRs with AI-generated descriptions | [Guide](guide/auto-pr.md) |
| **Vector Search** | SQLite-backed semantic code search | [Guide](guide/analyze.md#vector-search) |
| **Plugins** | Extend with custom scanners and reporters via entry points | [Guide](guide/plugins.md) |
| **TUI** | Interactive terminal UI for browsing results | [CLI](reference/cli.md) |
| **Export** | CSV + Markdown summaries after every walk | [Config](reference/config.md) |
| **Notifications** | Slack/Discord webhooks on deploy fail or health regression | [Config](reference/config.md) |
| **Snapshots** | LRU-managed DB snapshots for instant state restore | [Architecture](architecture.md) |

---

## Quick Install

```bash
pip install rebuild
```

Or with all optional features:

```bash
pip install "rebuild[full]"
```

---

## 30-second Example

```bash
# Initialise config in your repo
rebuild init /path/to/my-service

# Walk the last 14 days (dry-run, no deploy needed)
rebuild walk /path/to/my-service --deploy none --days 14 --dry-run

# Open the timeline dashboard
rebuild serve --results-dir /path/to/my-service/.rebuild
```

---

## Next Steps

- [Installation →](getting-started/installation.md)
- [Quick Start →](getting-started/quickstart.md)
- [Configuration reference →](reference/config.md)
- [CLI reference →](reference/cli.md)
- [Architecture →](architecture.md)
- [Case Study: c2004 →](case_study_c2004.md)
- [Changelog →](changelog.md)
