# Benchmarks

Performance measurements for rebuild's hot paths. Reproduce locally with:

```bash
python scripts/benchmark_scanner_cache.py --commits 30 --files 200 --churn 0.05
```

## Diff-aware scanner cache (Sprint 3 / 2026-05-07)

`ScannerService` now caches AST-parsed endpoints by file content hash. Across
sequential commits in a `rebuild walk`, unchanged files are skipped entirely.

### Synthetic benchmark — 30 commits

Generated repo of FastAPI route modules; each commit mutates a fraction of files.

| Files | Churn / commit | No cache | With cache | Speedup | Hit rate |
|------:|:--------------:|---------:|-----------:|--------:|---------:|
|   200 |       5 %      |  1.11 s  |   0.20 s   |  5.5×   |  91.8 %  |
|   500 |       5 %      |  3.41 s  |   0.52 s   |  6.6×   |  91.8 %  |
|   200 |      10 %      |  1.14 s  |   0.32 s   |  3.6×   |  82.7 %  |
|   200 |      20 %      |  1.15 s  |   0.39 s   |  2.9×   |  77.3 %  |
|   200 |      50 %      |  1.16 s  |   0.74 s   |  1.6×   |  46.2 %  |

Hardware: typical CI runner (2 vCPU, 8 GB RAM). Numbers vary ±10 %.

### Interpretation

- **5 % churn** matches a healthy mainline repo (3-5 files changed per commit).
  Expect **5–7×** speedup on the FastAPI scan path.
- **At 50 % churn**, the cache still helps (deduplication of identical
  modules across commits, e.g. unchanged `__init__.py` files).
- The **hit rate** measures cache effectiveness directly. Below 50 % the
  overhead of hashing approaches the cost of parsing — but never exceeds it.

### How to enable

The cache is **on by default** for any `ScannerService` instance. It is
process-local and bound to a single instance. `BasePipeline` constructs one
`ScannerService` per walk, so all daily scans share the cache automatically.

To disable for diagnostics:

```python
service = ScannerService(config)
for commit in commits:
    service.reset_cache()   # forces fresh parse on every commit
    service.execute(repo)
```

### What it doesn't cache

- OpenAPI HTTP scans (`_scan_via_openapi`) — these depend on a live service.
- Compose label scans (`_scan_via_compose_labels`) — file is small (1 file).
- `deta scan` subprocess output.

The cache only short-circuits the **AST parse + decorator walk** for Python
files, which is the dominant cost (95 %+ of `_scan_via_fastapi_routes` time
on c2004-scale repos).

### Future work

- **Persistent on-disk cache** (Sprint 5+): survive process restarts.
- **Git blob SHA keys**: when running inside a `git` checkout, use
  `git ls-files --stage` for sub-millisecond cache lookups instead of
  hashing file bytes.
