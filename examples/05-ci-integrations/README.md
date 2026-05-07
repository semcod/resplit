# CI Integration Recipes

Ready-to-use CI workflows for running `rebuild` on every commit / PR / nightly.

| File | Platform | Mode |
|------|----------|------|
| [`github-actions.yml`](github-actions.yml) | GitHub Actions | PR diff scan + nightly full walk |
| [`gitlab-ci.yml`](gitlab-ci.yml) | GitLab CI | Merge request scan + scheduled walk |
| [`circleci.yml`](circleci.yml) | CircleCI | Two workflows: `pr` and `nightly` |

## What these workflows do

1. **On every PR / merge request** — fast diff scan (`rebuild walk --dry-run --days 1 --deploy none`) + endpoint count check vs. main branch baseline.
2. **Nightly / scheduled** — full historical walk (`rebuild walk --days 30 --deploy docker-compose`) producing dashboard + timeline. Artifacts are uploaded for download.
3. **Coverage gate** (optional, GitHub example) — fails the PR if health regresses by >20pp vs. baseline.

## Customise for your project

Each YAML has comments marked `# CUSTOMISE:` for places to adjust:
- Repository name / branch
- Health-check URL & port
- `rebuild.yaml` location (default: repo root)
- Notification webhooks (Slack/Discord)

See also:
- [Configuration reference](../../docs/reference/config.md)
- [Walk guide](../../docs/guide/walk.md)
- [Auto-PR guide](../../docs/guide/auto-pr.md) — for opening PRs with rebuild's findings
