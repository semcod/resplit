# Analyze

> See also: [CLI Reference](../reference/cli.md#rebuild-analyze) · [Architecture](../architecture.md#3-intelligence-layer-analysis) · [Case Study: c2004](../case_study_c2004.md)

The `analyze` sub-commands inspect your codebase for structural and semantic issues.

## Duplicates

```bash
rebuild analyze duplicates /path/to/repo
rebuild analyze duplicates /path/to/repo --min-lines 4 --semantic
```

Finds structurally identical and semantically similar code fragments. Output groups duplicates by similarity and suggests which to extract.

## Services

```bash
rebuild analyze services /path/to/repo
```

Builds a dependency graph of Python services/classes. Detects import cycles.

## Git Truth

```bash
rebuild analyze truth /path/to/repo
```

Correlates git history with test results to identify the "best" version of each function — highest test pass rate and lowest complexity.

## Vector Search

```bash
# Build index
rebuild analyze vector-build /path/to/repo

# Query
rebuild analyze vector-query /path/to/repo "authentication middleware"
```

SQLite-backed semantic code search using sentence-transformers embeddings.

## Multi-repo

```bash
rebuild analyze multi-repo /repo-a /repo-b /repo-c
```

Cross-repository dependency and duplication analysis.
