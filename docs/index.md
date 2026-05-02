# rebuild

**Historical deployment analysis** — walk git history day by day, deploy each commit, test all endpoints, capture screenshots, and restore working fragments.

---

## What is rebuild?

`rebuild` answers the question: *"When exactly did this service break — and what was the last known-good commit?"*

It walks your git history, deploys each commit (or uses an already-running stack), exercises every discovered API endpoint, captures screenshots, and produces a rich HTML timeline showing health trends over time.

```
git history  →  deploy  →  test endpoints  →  capture screenshots  →  report
```

---

## Key Features

| Feature | Description |
|---|---|
| **Walk** | Iterate git history, deploy per commit, test all endpoints |
| **Analyze** | Detect code duplication, service graph cycles, semantic similarity |
| **Refactor** | AI-powered refactoring plans + automated execution |
| **Auto-PR** | Open GitHub/GitLab PRs with AI-generated descriptions |
| **Vector Search** | SQLite-backed semantic code search |
| **Plugins** | Extend with custom scanners and reporters via entry points |
| **TUI** | Interactive terminal UI for browsing results |
| **Export** | CSV + Markdown summaries after every walk |

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
