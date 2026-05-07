# Refactor

> See also: [CLI Reference](../reference/cli.md#rebuild-refactor) · [Auto-PR](auto-pr.md) · [Analyze](analyze.md)

## Generate a plan

```bash
rebuild refactor plan /path/to/repo
rebuild refactor plan /path/to/repo --ai   # AI-enhanced suggestions
```

Combines duplication analysis, service graph cycles, and similarity scores to produce a prioritised refactoring plan.

## Execute the plan

```bash
rebuild refactor execute /path/to/repo
rebuild refactor execute /path/to/repo --force   # skip confirmation
```

Applies safe refactoring transformations automatically.

## Generate a PR description

```bash
rebuild refactor pr /path/to/repo
```

Uses AI to write a professional PR description from the analysis results. Requires `OPENROUTER_API_KEY` in `.env`.
