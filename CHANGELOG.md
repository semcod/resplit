# Changelog

> See also: [README](README.md) · [Roadmap (TODO)](TODO.md) · [Architecture](docs/architecture.md) · [Usage Guide](docs/usage.md)

## [Unreleased]

## [0.1.24] - 2026-05-07

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update TODO.md
- Update docs/README.md
- Update docs/architecture.md
- Update docs/c2004.md
- Update docs/case_study_c2004.md
- Update docs/getting-started/configuration.md
- Update docs/getting-started/installation.md
- ... and 12 more files

### Other
- Update .code2llm_cache/CHANGELOG_1778076057551732162_10277.pkl
- Update .code2llm_cache/README_1778073907205054095_118441.pkl
- Update .code2llm_cache/README_1778076055686234576_4285.pkl
- Update .code2llm_cache/__init___1778076055686826248_239.pkl
- Update .code2llm_cache/accelerated_pipeline_1778074802983432886_17641.pkl
- Update .code2llm_cache/app_1778075845753026155_1881.pkl
- Update .code2llm_cache/cli_1778074856579013858_25963.pkl
- Update .code2llm_cache/config_loader_1778074847536915897_6599.pkl
- Update .code2llm_cache/deploy_service_1778074822346642874_17643.pkl
- Update .code2llm_cache/duplication_engine_1778074797738375987_13246.pkl
- ... and 28 more files

## [0.1.23] - 2026-05-07

### Changed
- **Documentation overhaul**: Updated [README.md](README.md), [TODO.md](TODO.md), CHANGELOG.md with cross-links to all [docs/*](docs/) pages
- **SUMD.md regenerated**: Full project analysis — 3722 functions, 161 classes, 167 files, CC̄ = 3.9
- **Version sync**: All docs now reference v0.1.23 consistently

### Docs
- Updated [README.md](README.md) — documentation table, project status, SUMD stats, quick start
- Updated [TODO.md](TODO.md) — all phases marked complete, Phase 17 roadmap added, cross-links
- Updated [docs/architecture.md](docs/architecture.md) — v0.1.23, 634 tests, 72% coverage
- Updated [docs/index.md](docs/index.md) — current stats, notification hooks
- Updated [docs/getting-started/installation.md](docs/getting-started/installation.md) — version
- Updated [docs/reference/cli.md](docs/reference/cli.md) — version, notification hooks
- Updated [docs/c2004.md](docs/c2004.md) — completed items, version
- Updated [SUMD.md](SUMD.md), [docs/README.md](docs/README.md), project/ files

## [0.1.22] - 2026-05-02

### Changed
- Version bump to 0.1.22

## [0.1.21] - 2026-05-02

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md

## [0.1.20] - 2026-05-02

### Fixed
- **PipelineEvent Import Fix**: Resolved `ImportError: cannot import name 'PipelineEvent' from 'rebuild.domain.events'` by moving `PipelineEvent` to `domain_events.py` as a legacy class, exporting it from `__init__.py`, and removing unnecessary imports from `pipeline.py` and `accelerated_pipeline.py` while keeping backward compatibility in `base_pipeline.py`.
- **Missing astor dependency**: Added `astor>=0.8` to dependencies for code generation in refactor executor.

### Changed
- refactoring
- refactoring
- refactoring
- refactoring

## [0.1.19] - 2026-05-01

### Docs
- Update README.md
- Update docs/architecture.md
- Update docs/usage.md

## [0.1.18] - 2026-05-01

### Docs
- Update README.md

## [0.1.17] - 2026-05-01

### Docs
- Update README.md

### Other
- Update infra-map.json
- Update rebuild/interfaces/cli.py
- Update rebuild/interfaces/commands/walk_command.py

## [0.1.16] - 2026-05-01

### Docs
- Update README.md
- Update examples/09-mvp-protocol/README.md

### Test
- Update tests/test_accelerator_extra.py
- Update tests/test_db_snapshot_extra.py
- Update tests/test_domain_infra.py
- Update tests/test_git_helpers_extra.py
- Update tests/test_interfaces_smoke.py
- Update tests/test_pipeline_extra.py
- Update tests/test_restore_override.py
- Update tests/test_smart_screenshot.py
- Update tests/test_worktree_db.py

### Other
- Update project/map.toon.yaml

## [0.1.15] - 2026-05-01

### Docs
- Update README.md

### Test
- Update tests/test_test_service.py

### Other
- Update project/duplication.toon.yaml
- Update rebuild/application/pipeline.py
- Update rebuild/application/services/deploy_service.py
- Update rebuild/application/services/scanner_service.py
- Update rebuild/application/services/test_service.py
- Update rebuild/domain/day_result.py
- Update rebuild/domain/endpoint.py
- Update rebuild/domain/models.py

## [0.1.14] - 2026-05-01

### Docs
- Update README.md
- Update docs/README.md

### Test
- Update tests/test_test_service.py

## [0.2.0] - 2026-05-01

### 🔥 Major: Full-Stack Testing & Intelligence Platform

**Auth & Testing:**
- **Auth Login**: Added `login_url` and `login_payload` for automatic token acquisition
- **Auth Headers**: Custom headers support via `auth:` config
- **Param Substitution**: `{param}` in OpenAPI paths replaced with values from `test_fixtures:`
- **Test Bodies**: Per-endpoint body configuration via `test_bodies:`
- **Response Time Tracking**: Measured and displayed in reports

**Reporting & Visualization:**
- **Failure Grouping**: Errors classified (auth, template, timeout, server, network)
- **Trend Charts**: Inline SVG health% trend visualization
- **Endpoint Diff**: Track added/removed endpoints between days
- **SSE Live Streaming**: Real-time event stream in dashboard (`/events`)
- **Modern UI**: Dark glassmorphism design with Outfit + JetBrains Mono fonts

**Deploy & Reliability:**
- **Deploy Retry**: Configurable retry with exponential backoff
- **Health Verbose**: Detailed curl output when health checks fail
- **Deploy Logs**: Full logs captured in `DayResult.deploy_log`
- **Replay Code Sync**: `docker cp` copies checkout to `/app` before restart
- **Code Overlay**: Handle read-only mounts via `/tmp/rebuild-overlay` + PYTHONPATH

**Manual Recovery:**
- **Manual Override**: `--patch-dir` to apply fixes to cloned repo before walk
- **Health Recovery**: Detect `rebuild-fix:<sha>` commits in clone for recovery
- **Git Diff Names**: `diff_names()` for smart test selection

**Accelerator Mode (10x):**
- **Sync Current State**: `sync_current_state()` for node_modules preservation
- **Git Worktree**: Shared clone with rsync overlay
- **Dockerfile Patcher**: Auto-patch for accelerator compatibility
- **DB Snapshots**: Fast database state restoration
- **Parallel Tests**: Dependency graph-based parallel execution
- **Smart Selection**: Git-diff based test selection

**Analysis & Intelligence:**
- **Semantic Embeddings**: `sentence-transformers` integration for conceptual similarity
- **Vector Search**: SQLite-backed vector index for rapid semantic lookup
- **Multi-Repo Analysis**: Cross-repo dependency and clone detection
- **Auto PR**: Automated PR creation with AI summaries
- **Evolution Viz**: D3.js code evolution playback
- **DSL**: Domain Specific Language for scripting
- **NLP**: Natural language command parsing

**Scanner Enhancements:**
- **FastAPI Routes**: AST-based route discovery from source code
- **Router Prefixes**: Automatic prefix extraction from APIRouter()
- **Template Paths**: Track original template vs resolved path

**CLI Commands:**
- `rebuild accelerator`: Ultra-fast walk mode
- `rebuild auto-pr`: Automated PR creation
- `rebuild evolution`: Code evolution visualization
- `rebuild dsl`: DSL command execution
- `rebuild nlp`: Natural language parsing
- `rebuild mvp`: MVP protocol server
- `rebuild analyze vector-build`: Build semantic index
- `rebuild analyze vector-query`: Semantic search
- `rebuild analyze multi-repo`: Cross-repo analysis

**Infrastructure:**
- **Event Service**: Real-time event bus for SSE streaming
- **Config Loader**: Unified `rebuild.yaml` loading with CLI merge
- **Patcher Service**: Manual override application
- **Override Service**: Patch directory application
- **PR Service**: GitHub/GitLab PR automation
- **Summary Service**: AI summary generation

**Fixes:**
- **Safe Clone**: `walk` never creates files in original repo (removed auto-init)
- **Clone Isolation**: `clone_for_walk()` creates `.rebuild/repo/` for safe checkouts
- **Checkout Force**: `git checkout --force` for uncommitted changes
- **History Format**: `history_service` handles new `results.json` dict format
- **Replay Health**: Replay mode only checks health, doesn't `compose up`
- **Reload by Name**: `docker restart <name>` without compose project dependency

**Dependencies:**
- Added `sentence-transformers>=2.7` optional dependency (semantic)
- Updated `full` optional dependency to include semantic

## [0.1.13] - 2026-05-01

### Docs
- Update README.md

### Other
- Update .rebuild_c2004_test/2026-04-30/results.json
- Update .rebuild_c2004_test/2026-04-30/results.toon
- Update .rebuild_c2004_test/2026-04-30/results.yaml
- Update .rebuild_c2004_test/history.json
- Update .rebuild_c2004_test/history.jsonl
- Update .rebuild_c2004_test/index.html
- Update .rebuild_c2004_test/walk_state.json
- Update architecture.html
- Update infra-map.json

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
[Unreleased]: https://github.com/semcod/resplit/compare/v0.1.23...HEAD
[0.1.23]: https://github.com/semcod/resplit/compare/v0.1.22...v0.1.23
[0.1.22]: https://github.com/semcod/resplit/compare/v0.1.21...v0.1.22
[0.1.21]: https://github.com/semcod/resplit/compare/v0.1.20...v0.1.21
[0.1.20]: https://github.com/semcod/resplit/compare/v0.1.19...v0.1.20
[0.1.19]: https://github.com/semcod/resplit/compare/v0.1.18...v0.1.19
[0.1.18]: https://github.com/semcod/resplit/compare/v0.1.17...v0.1.18
[0.1.17]: https://github.com/semcod/resplit/compare/v0.1.16...v0.1.17
[0.1.16]: https://github.com/semcod/resplit/compare/v0.1.15...v0.1.16
[0.1.15]: https://github.com/semcod/resplit/compare/v0.1.14...v0.1.15
[0.1.14]: https://github.com/semcod/resplit/compare/v0.1.13...v0.1.14
[0.1.13]: https://github.com/semcod/resplit/compare/v0.1.12...v0.1.13
[0.1.12]: https://github.com/semcod/resplit/compare/v0.1.11...v0.1.12
[0.1.11]: https://github.com/semcod/resplit/compare/v0.1.10...v0.1.11
[0.1.10]: https://github.com/semcod/resplit/compare/v0.1.9...v0.1.10
[0.1.9]: https://github.com/semcod/resplit/compare/v0.1.0...v0.1.9
[0.1.0]: https://github.com/semcod/resplit/releases/tag/v0.1.0
