# Auto-PR

`rebuild auto-pr` opens a pull/merge request on GitHub or GitLab with an AI-generated description from the latest analysis results.

## Setup

```bash
# GitHub
export REBUILD_PR_PLATFORM=github
export REBUILD_PR_TOKEN=ghp_xxx
export REBUILD_PR_OWNER=my-org
export REBUILD_PR_REPO=my-repo
export REBUILD_PR_BASE=main
export REBUILD_PR_HEAD=feature/refactor

# GitLab
export REBUILD_PR_PLATFORM=gitlab
export REBUILD_PR_TOKEN=glpat_xxx
export REBUILD_PR_OWNER=my-group
export REBUILD_PR_REPO=my-project
```

## Run

```bash
rebuild auto-pr /path/to/results.json
```

## What it does

1. Reads analysis results from the JSON file
2. Calls `SummaryService` to generate an AI summary
3. Opens a PR/MR via the GitHub or GitLab API
4. Prints the PR URL

## Environment variables

| Variable | Description |
|---|---|
| `REBUILD_PR_PLATFORM` | `github` or `gitlab` |
| `REBUILD_PR_TOKEN` | Personal access token |
| `REBUILD_PR_OWNER` | Org/user (GitHub) or group (GitLab) |
| `REBUILD_PR_REPO` | Repository name |
| `REBUILD_PR_BASE` | Base branch (default: `main`) |
| `REBUILD_PR_HEAD` | Head branch to merge |
| `REBUILD_PR_TITLE` | PR title (optional) |
