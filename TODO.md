# TODO: rebuild Roadmap

> **Current version:** v0.1.30 · **Tests:** 829 · **Coverage:** 77%
>
> See also: [README](README.md) · [Changelog](CHANGELOG.md) · [Docs Hub](docs/index.md) · [Analysis (P1–P4)](ANALYSIS.md) · [Architecture](docs/architecture.md) · [Usage Guide](docs/usage.md)
>
> **Note:** Completed work moved to CHANGELOG:
> - **Phases 10–16** → [Completed Roadmap](CHANGELOG.md#completed-roadmap--phases-1016)
> - **Sprint 1** (Quality Gates + Infra) → [`[Unreleased] § Sprint 1`](CHANGELOG.md#sprint-1--quality-gates--infra-foundation-2026-05-07)
> - **Sprint 2** (Konsolidacja Duplikatów) → [`[Unreleased] § Sprint 2`](CHANGELOG.md#sprint-2--konsolidacja-duplikatów-2026-05-07)
> - **Sprint 3** (Showcase + Performance) → [`[Unreleased] § Sprint 3`](CHANGELOG.md#sprint-3--showcase--performance-2026-05-07)
> - **Sprint 4** (Watch + Mutation) → [`[Unreleased] § Sprint 4`](CHANGELOG.md#sprint-4--reuse-bibliotek--watch-mode-2026-05-07-partial)
> - **Sprint 4c** (Analyze Services Bug Fixes) → [`[Unreleased] § Sprint 4c`](CHANGELOG.md#sprint-4c--analyze-services-bug-fixes-2026-05-07)
> - **Sprint 5a** (Prometheus /metrics) → [`[Unreleased] § Sprint 5a`](CHANGELOG.md#sprint-5a--prometheus-metrics-endpoint-2026-05-08)
> - **Sprint 5b** (Reporter Refactor + Endpoint-Trend Konsolidacja) → [`[Unreleased] § Sprint 5b`](CHANGELOG.md#sprint-5b--reporter-refactor--endpoint-trend-konsolidacja-2026-05-08)

---

## Phase 17 — Next Steps (PLANNED)

Pre-existing roadmap items, kept for continuity. See [ANALYSIS.md](ANALYSIS.md) Sprints 5+ for sequencing.

### 🔴 Krytyczne
- [ ] **c2004 Full Walk (30 days)**: Uruchomić `rebuild walk` z `--deploy docker-compose --days 30` na c2004. Skrypt gotowy: [`scripts/run_c2004_full.sh`](scripts/run_c2004_full.sh).
- [ ] **Performance Profiling**: Profilowanie walk na dużych repo (>500 commitów) — targetowane <5min/commit. Diff-aware cache (Sprint 3) daje już 5.5-6.6× speedup w fazie scan; teraz potrzebny pełny end-to-end profiling.
- [ ] **Test Coverage ≥80%**: Następny milestone (obecnie 77%) — przetestować pozostałe edge cases w `pipeline/services`, refactor `reporter.py`.

### 🟠 Wysokie
- [ ] **TestQL Integration**: Natywna integracja z `testql` DSL — zastąpienie `dsl.py` + `dsl_v2.py`. Wymaga eksploracji submodułów (1.x ma puste top-level eksporty).
- [ ] **`regres` integracja**: zastąpienie `regression_service` (Sprint 2). Pakiet eksportuje moduły CLI, nie czyste API — adapter lub wait-for-API-cleanup.
- [ ] **E2E test harness** (`tests/e2e/test_full_walk.py`): wymaga env z docker. Odroczone z Sprint 3.
- [ ] **Report Templates**: Konfigurowalne szablony raportów HTML (Jinja2).

### 🟡 Średnie
- [ ] **Web Dashboard**: Standalone web UI (React/Next.js) z real-time SSE.
- [x] **Grafana Integration** (Sprint 5a): `/metrics` endpoint w `rebuild/interfaces/api/metrics.py` z 6 metrykami (HTTP requests, latency, walks, cache hits/misses, WS connections). Patrz [CHANGELOG: Sprint 5a](CHANGELOG.md#sprint-5a--prometheus-metrics-endpoint-2026-05-08).
- [ ] **VS Code Extension**: Wyświetlanie wyników rebuild w edytorze.
- [x] **Refactor `reporter.py`** (Sprint 5b): 434 → 120 LOC (-72%). Split na `day_html.py`, `timeline_html.py`, `summary_export.py`, `_html_assets.py` + nowy `endpoint_trend_service.py`. Patrz [CHANGELOG: Sprint 5b](CHANGELOG.md#sprint-5b--reporter-refactor--endpoint-trend-konsolidacja-2026-05-08).
- [ ] **`release-please` migracja**: Zastąp `scripts/bump_version.py` + `auto_bump.yml`.
- [ ] **Differential mutation testing** ([`docs/mutation_testing.md`](docs/mutation_testing.md) § Future work): mutować tylko pliki zmienione w PR, gate ≥80 % na te pliki.
- [ ] **Persistent on-disk scanner cache** ([`docs/benchmarks.md`](docs/benchmarks.md) § Future work): przeżycie process restart, klucze przez `git ls-files --stage`.
