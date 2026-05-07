# Changelog

> See also: [README](README.md) · [Roadmap (TODO)](TODO.md) · [Analysis (P1–P4)](ANALYSIS.md) · [Architecture](docs/architecture.md) · [Usage Guide](docs/usage.md)

## Completed Roadmap — Phases 10–16

Aggregated summary of completed work, moved here from `TODO.md` on 2026-05-07.
Detailed per-version notes appear in entries below.

### Phase 10 — c2004 Testing & Improvements ✅ (sesja 2026-05-01, v0.1.13–v0.1.18)
- **Clone for walk**: Pipeline klonuje repo do `.rebuild/repo/` — oryginał nienaruszony
- **git checkout --force**: Bezpieczne przełączanie commitów w klonie
- **Replay mode fix**: `start()` w replay tylko sprawdza health, nie uruchamia nowego compose
- **Replay reload**: `docker restart <name>` bezpośrednio po nazwie kontenera
- **history_service**: Obsługa nowego formatu `results.json` (dict z kluczem `results`)
- **index.html**: Eksport JSON/YAML/TOON + toolbar w nawigacji
- **`rebuild serve`**: Komenda do serwowania raportów na HTTP
- **Deploy Log Details**: Pełne docker logs w `DayResult` + raporty failed deployów
- **Param Substitution**: OpenAPI/FastAPI scanner — `{param}` → wartości z `rebuild.yaml`
- **Fixture Seed**: `test_fixtures:` w `rebuild.yaml`
- **Auth Config**: `auth:` w `rebuild.yaml` dla custom headers (Bearer tokens)
- **Replay + volume mount**: Code mount per commit zamiast obrazu
- **`init` w klonie**: Nie modyfikuje oryginalnego repo
- **Deploy Retry**: Retry z backoff dla niestabilnych deployów
- **Health Check Verbose**: Szczegółowy log curl output przy fail
- **Manual Override**: `patch/` directory w `.rebuild/` z auto-applied fixes
- **Token Propagation**: Login raz, propagacja Bearer do wszystkich requestów
- **Per-Endpoint Body**: `body:` dla POST/PUT/PATCH w konfiguracji
- **Failure Grouping**: Raport HTML grupuje błędy (auth/template/missing)
- **Trend Chart**: Health% w czasie (Chart.js / SVG inline)
- **Endpoint Diff**: Endpointy znikłe/nowe między commitami
- **Response Time Tracking**: `time_ms` dla wszystkich requestów
- **Analyze c2004**: `duplicates` (1597 grup), `services`, `truth` na wybrane moduły

### Phase 11 — Deep Semantic Analysis ✅
- **Semantic Embeddings**: `sentence-transformers` w `duplication_engine` → [Analyze docs](docs/guide/analyze.md#vector-search)
- **Vector Search**: SQLite-backed vector DB → [CLI: vector-build/vector-query](docs/reference/cli.md#rebuild-analyze-vector-build-path)

### Phase 12 — Real-time & Cross-Repo ✅
- **Multi-Repo Support**: Cross-repo dependency analysis → [Analyze: multi-repo](docs/guide/analyze.md#multi-repo)
- **Real-time Monitoring**: Live SSE event log w dashboard → [Visualization](docs/usage.md#6-visualization)
- **Auto-PR Agent**: Auto PRs na GitHub/GitLab → [Auto-PR docs](docs/guide/auto-pr.md)

### Phase 13 — UI/UX Refinement ✅
- **D3.js Code Evolution**: Playback graf zależności w czasie
- **TUI Refactor**: Domain logic wyodrębniona z `interfaces/tui.py`

### Phase 14 — Production Readiness ✅ (ukończone 2026-05-01)
- **Test Coverage ≥60%**: 347 testów, 60% coverage
- **`--health-timeout` CLI**: Dla dużych stacków → [CLI Reference](docs/reference/cli.md#rebuild-walk)
- **Deploy Error Classification**: `compose_build_fail`, `port_conflict`, `migration_fail`, `missing_env` → [Architecture: Deploy Error](docs/architecture.md#deploy-error-classification)
- **Documentation Update**: `docs/usage.md`, `docs/architecture.md`, `README.md`
- **Service Table**: Kompletna tabela usług → [Architecture: Key Services](docs/architecture.md#key-services)

### Phase 15 — c2004 Integration & Stability ✅
- **c2004 npm ci fix**: `if [ -f package-lock.json ]; then npm ci; else npm install; fi`
- **c2004 Walk z `--deploy none`**: 442 endpointy w 1-day test walk
- **Config Validation**: Pydantic schema dla `rebuild.yaml` + czytelne błędy
- **PipelineEvent Import Fix**: Przeniesione do `domain_events.py` jako legacy class
- **Walk Result Regression Guard**: Auto-flag spadku health% >20%
- **c2004 Dashboard**: 444 endpointów wyświetlane poprawnie
- **`--output` respects rebuild.yaml**: `output.dir` z YAML nadpisuje domyślne `.rebuild`
- **Deploy log truncation**: Limit 200 linii w `results.json` z info o obcięciu
- **Health verbose summary**: Status + first 200 bytes body przy fail
- **Endpoint count diff warning**: Ostrzeżenie przy zmianie >10% między dniami

### Phase 16 — Production Release ✅
- **PyPI Package**: `rebuild` na PyPI v0.1.20 → [PyPI](https://pypi.org/project/rebuild/)
- **CI/CD Pipeline**: GitHub Actions — testy, ruff, coverage gate ≥70% → [`.github/workflows/`](.github/workflows/)
- **Semantic Versioning**: Auto-bump z CHANGELOG → `scripts/bump_version.py`
- **Docker Image**: `ghcr.io/semcod/rebuild:latest` → `Dockerfile` + `.github/workflows/docker.yml`
- **Config Validation (pydantic)**: `RebuildConfig`, `ConfigSchemaValidator`, `load_and_validate()` → [Config Reference](docs/reference/config.md)
- **Plugin System**: `BaseScanner`, `BaseReporter`, `PluginRegistry`, entry points `rebuild.scanners`/`rebuild.reporters`, `rebuild plugins` CLI → [Plugin docs](docs/guide/plugins.md)
- **Documentation Site**: MkDocs Material → [GitHub Pages](https://semcod.github.io/resplit)
- **TUI Full Features**: j/k navigation, g/G, live log, endpoint browser
- **Export Formats**: CSV + Markdown summary
- **Notification Hooks**: Slack/Discord webhooks na deploy fail / health regression → [Config Reference](docs/reference/config.md)
- **Snapshot Management**: LRU cache, `max_snapshots`, `_auto_prune()`, `prune_old(keep=N)`, `stats()`
- **Test Coverage ≥70%**: Osiągnięto 72% (634 testów)

---

## [Unreleased]

### Sprint 1 — Quality Gates + Infra Foundation (2026-05-07)

Hardening pipeline'u CI bez zmian architektury. Patrz [ANALYSIS.md](ANALYSIS.md) Sprint 1.

#### Added
- **`.pre-commit-config.yaml`** — ruff (lint+format), mypy (non-blocking), built-in hygiene hooks (trailing-ws, eof, check-yaml/toml/large-files, debug-statements)
- **`docker-compose.example.yml`** — przykład deployment z rebuild + dashboard + repo mount na `localhost:7821`
- **`ANALYSIS.md`** — kompletna analiza P1–P4 + plan sprintów 1–5+ wzorowana na metodologii Semcod GitHub App

#### Changed
- **`.github/workflows/ci.yml`** — dodany krok `mypy` jako `continue-on-error` (non-blocking, gotowy do promowania w Sprincie 3)
- **`.github/workflows/docker.yml`** — multi-arch build `linux/amd64,linux/arm64` + `setup-qemu-action@v3`. Krytyczne dla testowania na ARM (case c2004).
- **`TODO.md`** — przeniesione Phasy 10–16 do [CHANGELOG: Completed Roadmap](#completed-roadmap--phases-1016); zostawione tylko Phase 17 + plan sprintów

#### Fixed
- **Ruff config bug** w [`.github/workflows/ci.yml`](.github/workflows/ci.yml): usunięte `--ignore W503` (W503 to flake8 pseudo-rule, nieistniejąca w ruff). CI fail-ował natychmiast przy lint step.
- **354 błędów stylu w `rebuild/`**: 302 auto-fix (whitespace, redundant f-strings, etc.) + 52 unsafe-fix (W291, W293) + 7 ręcznych E701 (`if x: continue` → wieloliniowe) + 3 brakujące importy F821:
  - `rebuild/application/services/override_service.py`: `Optional` z `typing`
  - `rebuild/infrastructure/shell_adapter.py`: `Path` z `pathlib` (×2)

### Sprint 2 — Konsolidacja Duplikatów (2026-05-07)

Refactor niskiego ryzyka eliminujący duplikaty wskazane w [ANALYSIS.md](ANALYSIS.md) §P1.

#### Added
- **`rebuild/application/services/regression_service.py`** — single source of truth dla detekcji regresji health-pct.
  - Public: `compute_health_trend(results, threshold) -> List[HealthTrendPoint]`
  - Adapter dict (dla `reporter.py`): `compute_health_trend_dict(results, threshold) -> dict[day, label]`
  - Adapter list (dla `helpers.py`): `compute_health_trend_labels(results, threshold) -> List[str]`
  - Stała: `DEFAULT_REGRESSION_THRESHOLD_PP = 20.0`
  - Frozen dataclass `HealthTrendPoint(day, health_pct, delta, label, is_regression)`
- **`collect_cli_overrides(ctx, names)`** w `rebuild/interfaces/commands/helpers.py` — eliminuje 14× duplikat `ctx.get_parameter_source(name) == ParameterSource.COMMANDLINE` w typer commands.

#### Changed
- **`rebuild/application/services/reporting/reporter.py:_health_trend_by_day`** → cienki adapter delegujący do `regression_service.compute_health_trend_dict`. Public method signature i zachowanie zachowane (subclass-safe).
- **`rebuild/interfaces/commands/helpers.py:compute_health_trend_labels`** → cienki adapter delegujący do `regression_service.compute_health_trend_labels`. Public function signature zachowana — wszystkie istniejące testy i importy działają bez zmian.
- **`rebuild/interfaces/cli.py:walk()`** zredukowane z 44 LOC body do 13 LOC. Usunięty nieużywany import `from click.core import ParameterSource`.

#### Deprecated
- **`rebuild.domain.dsl`** (legacy v1): dodany `DeprecationWarning` przy imporcie modułu + `.. deprecated:: 0.1.26` w docstringu. Pełne usunięcie odroczone do Sprintu 4 — `dsl_v2` nie pokrywa wszystkich komend (`evolution`, `auto_pr`, `restore`, `serve`); pełnym zamiennikiem będzie `testql` (PyPI v0.6.18).
- **`Endpoint.testql_passed`** field: explicit komentarz że to placeholder na Sprint 4 (currently never populated by walk/test pipelines).

#### Verification
- `ruff check rebuild/ --select E,W,F --ignore E501` → **All checks passed**
- `pytest -k "trend or regression or health"` → 8 passed (pełna pokrywalność migracji)
- `pytest`: 631 passed, 3 preexisting failures (`TestCLISubprocessE2E.*` — środowiskowy `No module named rebuild`, nie regresja)

---

## [0.1.26] - 2026-05-07

### Docs
- Update ANALYSIS.md
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update .gitignore
- Update .pre-commit-config.yaml
- Update .rebuild_c2004_test/2026-04-30/results.json
- Update .rebuild_c2004_test/2026-04-30/results.toon
- Update .rebuild_c2004_test/2026-04-30/results.yaml
- Update .rebuild_c2004_test/history.json
- Update .rebuild_c2004_test/history.jsonl
- Update .rebuild_c2004_test/index.html
- Update .rebuild_c2004_test/walk_state.json
- Update .rebuild_ev/2026-05-01/commit.txt
- ... and 71 more files

## [0.1.25] - 2026-05-07

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md

### Other
- Update app.doql.less
- Update project/map.toon.yaml

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
