# Changelog

## [Unreleased]

## [0.1.12] - 2026-05-01

### Docs
- Update README.md
- Update docs/case_study_c2004.md
- Update docs/img/c2004_dashboard.png
- Update docs/img/c2004_duplication.png
- Update docs/img/c2004_graph.png
- Update docs/img/c2004_tasks.png

### Test
- Update tests/test_deploy_service.py
- Update tests/test_models.py
- Update tests/test_reporter_service.py

### Other
- Update architecture.html
- Update rebuild/application/pipeline.py
- Update rebuild/application/services/deploy_service.py
- Update rebuild/application/services/history_service.py
- Update rebuild/application/services/reporter_service.py
- Update rebuild/application/services/scanner_service.py
- Update rebuild/application/services/test_service.py
- Update rebuild/domain/day_result.py
- Update rebuild/domain/models.py
- Update rebuild/interfaces/cli.py
- ... and 1 more files

## [0.1.11] - 2026-05-01

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/usage.md

### Test
- Update tests/test_pipeline.py

### Other
- Update .rebuild_ev/2026-05-01/commit.txt
- Update .rebuild_ev/2026-05-01/endpoints.json
- Update .rebuild_ev/2026-05-01/results.json
- Update .rebuild_ev/history.jsonl
- Update .rebuild_ev/index.html
- Update .rebuild_inc/2026-05-01/commit.txt
- Update .rebuild_inc/2026-05-01/endpoints.json
- Update .rebuild_inc/2026-05-01/results.json
- Update .rebuild_inc/history.jsonl
- Update .rebuild_inc/index.html
- ... and 7 more files


## [0.1.10] - 2026-05-01
### 🔥 Major: Code Evolution Intelligence Engine
- **Intelligence Layer**: Added AST-based duplication detection, Service Dependency Graphs, and Git Truth Ranking.
- **Decision Engine**: Introduced `reactor` command group for automated Refactor Planning and Execution.
- **AI Integration**: Integrated **LiteLLM** (via OpenRouter) for AI-powered refactor summaries and automated PR generation.
- **Event Sourcing**: Implemented append-only `history.jsonl` to track all pipeline actions (Audit Log).
- **Architecture**: Refactored to a strict 5-layer design with **CQRS** (Commands/Queries) and **Infrastructure Adapters**.

### ⚡ Added
- `rebuild init`: Automated project bootstrapping with `rebuild.yaml` and `.env`.
- `rebuild analyze graph --export`: Interactive D3.js architecture visualization.
- `rebuild walk --incremental`: Performance optimization to skip processed commits.
- **Multi-Language Support**: Duplication detection now supports **JS/TS/JSX/TSX** files.

### 🛡️ Fixed & Improved
- **Docker Isolation**: Enhanced with unique project names (`-p`) and volume cleanup (`-v`).
- **Resilient Probing**: `HttpAdapter` with exponential backoff for health checks.
- **Unified CLI**: Simplified command structure with `analyze` and `refactor` subcommands.

## [0.1.9] - 2026-04-30
### Added
- Layered architecture: `interfaces/`, `application/`, `domain/`.
- `HistoryService` for results management.
- Standardized `Service` protocol for all pipeline steps.

## [0.1.0] - 2026-04-15
- Initial release as `rebuild` deployment tool.
