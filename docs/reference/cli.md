# CLI Reference

> See also: [Config Reference](config.md) · [Architecture](../architecture.md) · [Usage Guide](../usage.md)

## Global options

```
rebuild --help
rebuild version
```

---

## `rebuild walk`

Walk git history and test each commit.

```
rebuild walk REPO [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--days N` | `30` | Number of days to walk |
| `--date-from YYYY-MM-DD` | — | Start date |
| `--date-to YYYY-MM-DD` | — | End date |
| `--deploy METHOD` | `auto` | `none`, `docker-compose`, `auto`, `custom` |
| `--output DIR` | `.rebuild` | Output directory |
| `--health-url URL` | `http://localhost:8000/health` | Health check endpoint |
| `--base-url URL` | `http://localhost:8000` | Base URL for endpoint testing |
| `--health-timeout N` | `60` | Health check timeout (seconds) |
| `--screenshots / --no-screenshots` | off | Capture screenshots with Playwright |
| `--dry-run` | off | Skip deploy, test endpoints on running stack |
| `--replay` | off | Replay mode — reuse existing containers |
| `--serve` | off | Auto-start HTTP server after walk |
| `--port N` | `7821` | Port for `--serve` |
| `--accelerator` | off | Use AcceleratedPipeline with DB snapshots |

---

## `rebuild analyze`

### `rebuild analyze duplicates PATH`

Detect duplicate code fragments.

| Option | Default | Description |
|---|---|---|
| `--min-lines N` | `6` | Minimum lines per fragment |
| `--semantic` | off | Enable semantic (embedding) similarity |
| `--semantic-model NAME` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `--semantic-threshold F` | `0.85` | Similarity threshold (0–1) |

### `rebuild analyze services PATH`

Build and display the service dependency graph.

### `rebuild analyze truth PATH`

Analyse function quality using git history and test results.

### `rebuild analyze vector-build PATH`

Build a vector search index from code fragments.

### `rebuild analyze vector-query PATH QUERY`

Semantic search in the vector index.

### `rebuild analyze multi-repo PATH [PATHS...]`

Cross-repository dependency and duplication analysis.

---

## `rebuild refactor`

### `rebuild refactor plan PATH`

Generate a refactoring plan.

| Option | Default | Description |
|---|---|---|
| `--ai` | off | Use AI to enhance suggestions |

### `rebuild refactor execute PATH`

Execute the refactoring plan.

| Option | Default | Description |
|---|---|---|
| `--force` | off | Skip confirmation prompt |

### `rebuild refactor pr PATH`

Generate a PR description (requires AI key).

---

## `rebuild plugins`

List installed scanner and reporter plugins.

```bash
rebuild plugins
rebuild plugins --verbose
```

---

## `rebuild init PATH`

Initialise a new rebuild project.

```bash
rebuild init /path/to/repo
rebuild init /path/to/repo --force   # overwrite existing files
```

---

## `rebuild serve`

Serve walk results over HTTP.

```bash
rebuild serve --results-dir .rebuild --port 7821
```

---

## `rebuild report`

Print a summary of walk results.

```bash
rebuild report --results-dir .rebuild
```

---

## `rebuild version`

Print the installed version.

```bash
rebuild version
# rebuild v0.1.23
```

---

## `rebuild tui`

Launch the interactive terminal UI.

```bash
rebuild tui
```

Requires `pip install "rebuild[tui]"`.

---

## `rebuild accelerator`

Ultra-fast walk using git worktrees and DB snapshots.

```bash
rebuild accelerator /path/to/repo --service backend --parallel 4 --smart
```

See [Usage Guide: Accelerator Mode](../usage.md#9-accelerator-mode-10x-faster).
