# TODO: rebuild Roadmap

> **Current version:** v0.1.25 · **Tests:** 634 · **Coverage:** 72%
>
> See also: [README](README.md) · [Changelog](CHANGELOG.md) · [Analysis (P1–P4)](ANALYSIS.md) · [Architecture](docs/architecture.md) · [Usage Guide](docs/usage.md)
>
> **Note:** Completed Phases 10–16 moved to [CHANGELOG — Completed Roadmap](CHANGELOG.md#completed-roadmap--phases-1016) on 2026-05-07.

---

## Phase 17 — Next Steps (PLANNED)

Pre-existing roadmap items, kept for continuity. See [ANALYSIS.md](ANALYSIS.md) Sprints 3–5 for sequencing.

### 🔴 Krytyczne
- [ ] **c2004 Full Walk (30 days)**: Uruchomić `rebuild walk` z `--deploy docker-compose --days 30` na c2004 (Sprint 3)
- [ ] **Performance Profiling**: Profilowanie walk na dużych repo (>500 commitów) — targetowane <5min/commit (Sprint 3)
- [ ] **Test Coverage ≥80%**: Następny milestone — przetestować pozostałe edge cases w pipeline/services (Sprint 3)

### 🟠 Wysokie
- [ ] **TestQL Integration**: Natywna integracja z `testql` DSL — zastąpienie `dsl.py` + `dsl_v2.py` (Sprint 4)
- [ ] **Diff-aware Scanning**: Skanowanie tylko zmienionych endpointów (Sprint 2)
- [ ] **Report Templates**: Konfigurowalne szablony raportów HTML (Jinja2) (Sprint 5+)

### 🟡 Średnie
- [ ] **Web Dashboard**: Standalone web UI (React/Next.js) z real-time SSE (Sprint 5+)
- [ ] **Grafana Integration**: Eksport metryk health% do Prometheus/Grafana (Sprint 5+)
- [ ] **VS Code Extension**: Wyświetlanie wyników rebuild w edytorze (Sprint 5+)

---

## Sprint Plan (z [ANALYSIS.md](ANALYSIS.md))

### Sprint 1 — Quality Gates + Infra Foundation (tydzień 1–2) ✅ UKOŃCZONY (2026-05-07)

Najtańszy zwrot: hardening bez zmian architektury.

- [x] **Pre-commit hooks**: [`.pre-commit-config.yaml`](.pre-commit-config.yaml) z ruff + mypy + check-yaml/toml/large-files
- [x] **CI matrix**: Python 3.11 + 3.12 + 3.13 w [`.github/workflows/ci.yml`](.github/workflows/ci.yml) *(już było)*
- [x] **Coverage gate ≥70%**: w [`.github/workflows/ci.yml`](.github/workflows/ci.yml) *(już było)*
- [x] **mypy w CI**: Dodany jako `continue-on-error` step (non-blocking, gotowe do promowania w Sprint 3)
- [x] **Dockerfile multi-arch**: `linux/amd64,linux/arm64` + QEMU w [`.github/workflows/docker.yml`](.github/workflows/docker.yml)
- [x] **mkdocs build --strict**: w [`.github/workflows/docs.yml`](.github/workflows/docs.yml) *(już było)*
- [x] **docker-compose.example.yml**: [`docker-compose.example.yml`](docker-compose.example.yml) z rebuild + dashboard + repo mount
- [x] **Ruff bug fix**: usunięte niepoprawne `--ignore W503` (nie istnieje w ruff). Auto-fix 354 błędów stylu (302 + 52 unsafe) + ręcznie 7 × E701 + 3 × F821 (`Optional`/`Path` missing imports)

### Sprint 2 — Konsolidacja Duplikatów (tydzień 3–4) ✅ UKOŃCZONY (2026-05-07)

Refactor niskiego ryzyka, eliminuje long-tail dług techniczny.

- [x] **`regression_service.py`** ([source](rebuild/application/services/regression_service.py)): Wyciąg z 3 miejsc → `compute_health_trend()` + adaptery `compute_health_trend_dict()` (dla `reporter.py`) i `compute_health_trend_labels()` (dla `helpers.py`). Public API zachowane — wszystkie 8 testów regresji nadal pass.
- [x] **Refactor `cli.py:walk()`** (44 LOC → 13 LOC body): nowy helper `collect_cli_overrides(ctx, names)` w [`helpers.py`](rebuild/interfaces/commands/helpers.py) eliminuje 14× duplikat `ctx.get_parameter_source(...)`. Usunięty nieużywany `from click.core import ParameterSource`.
- [x] **Deprecation `dsl.py`**: dodany `DeprecationWarning` przy imporcie + `.. deprecated:: 0.1.26` w docstringu. **Pełne usunięcie odroczone do Sprintu 4** — `dsl_v2.py` nie pokrywa wszystkich komend (brak `evolution`, `auto_pr`, `restore`, `serve`); pełny zamiennik to `testql` (PyPI) w Sprincie 4.
- [x] **Decyzja `Endpoint.testql_passed`**: zachowane jako placeholder na Sprint 4 z explicit komentarzem (NIGDY nie populowane przez walk/test pipelines, serializowane jako None).
- [x] **Diff-aware scanning** (P17 #5): zrealizowane w Sprincie 3 (zob. niżej).

### Sprint 3 — Showcase + Performance (tydzień 5–6) ✅ UKOŃCZONY (2026-05-07)

Materiał marketingowy + dowód wydajności.

- [x] **c2004 Full 30-day Walk** ([`scripts/run_c2004_full.sh`](scripts/run_c2004_full.sh)): pre-flight checks (rebuild/git/docker), auto-clone c2004, walk + dashboard, summary stats. `SKIP_DEPLOY=1` dla dry-run.
- [x] **`scripts/benchmark_scanner_cache.py`** + [`docs/benchmarks.md`](docs/benchmarks.md): kontent-hash cache eliminuje powtórne parsowanie AST między commitami. Pomierzony **5.5–6.6× speedup** przy realistycznych parametrach (200-500 plików, 5% churn, hit rate 91.8%).
- [x] **Diff-aware scanning**: `ScannerService._endpoints_for_python_file()` z cache by content SHA-1. Public API: `cache_stats`, `reset_cache()`. Cache jest automatycznie używany przez `BasePipeline` (jeden ScannerService per walk).
- [x] **CI integration recipes**: [`examples/05-ci-integrations/`](examples/05-ci-integrations/) — `github-actions.yml` (PR scan + nightly walk + auto-comment), `gitlab-ci.yml` (MR scan + scheduled), `circleci.yml` (workflows pr+nightly), README z guide.
- [x] **Coverage 75% → 77%** (cel 80% odroczony do Sprint 5+): `plugins/` 0→100%, `interfaces/api/app.py` 58→78%. **Bonus: naprawiony realny bug** w API — wszystkie 4 command endpointy (`/commands/walk|analyze|snapshot|prune`) zwracały 422 Unprocessable Entity z powodu `from __future__ import annotations` + brak `Body(...)`. Po fix endpointy działają.
- [ ] **E2E test harness** (`tests/e2e/test_full_walk.py`): odroczone do Sprint 4 (wymaga env z docker).

### Sprint 4 — Reuse Bibliotek + Watch Mode (tydzień 7–8) 🟦 CZĘŚCIOWO UKOŃCZONY (2026-05-07)

Wreszcie używamy `[full]` extras (`wup`, `regres`, `testql`).

- [x] **`wup` integracja → `rebuild watch`**: nowa komenda CLI używa `wup.WupWatcher` jako optional dep. Pełna konfiguracja przez `WupConfig`/`WatchConfig` (excludes `.git`, `.venv`, `node_modules`, `.rebuild`). Custom `on_change` handler wywołuje `rebuild walk --dry-run`. 12 testów (`tests/test_watch_command.py`) z mockowanym watcherem i fail-graceful gdy wup brak. Nowe extras: `[watch]` i `[api]`. Zob. [`watch_command.py`](rebuild/interfaces/commands/watch_command.py).
- [x] **Mutation testing infrastructure**: `[tool.mutmut]` w pyproject.toml, [`scripts/run_mutation_tests.sh`](scripts/run_mutation_tests.sh) z threshold gate (default 75%), [`.github/workflows/mutation.yml`](.github/workflows/mutation.yml) nightly @ 03:00 UTC, [`docs/mutation_testing.md`](docs/mutation_testing.md) z guide. **Mutmut dodany do `dev` extras** — uruchomienie wymaga `pip install -e .[dev]`.
- [ ] **`testql` integracja** (P17 — zastąpienie `dsl.py`): odroczone do **Sprint 5+**. testql 1.x ma puste top-level eksporty — wymaga osobnej sesji eksploracji submodułów.
- [ ] **`regres` integracja** (zastąpienie Sprint 2 `regression_service`): odroczone do **Sprint 5+**. regres eksportuje moduły CLI (`doctor`, `defscan`), nie czyste API Pythonowe — wymaga adaptera albo wait-for-API-cleanup.

### Sprint 5+ — Ecosystem Extensions

Niska priorytet, jednorazowe inwestycje.

- [ ] **Grafana / Prometheus exporter**: `/metrics` endpoint (~50 LOC)
- [ ] **Refactor `reporter.py` (452 LOC)**: Split na `health_reporter.py`, `chart_reporter.py`, `summary_reporter.py`
- [ ] **VS Code extension** (P17): Wyświetlanie wyników w edytorze
- [ ] **Web Dashboard (React)** (P17): Tylko jeśli prawdziwa potrzeba użytkowników
- [ ] **`release-please` migracja**: Zastąp `scripts/bump_version.py` + `auto_bump.yml`
- [ ] **Report Templates** (P17): Jinja2 dla custom HTML
