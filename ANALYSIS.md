# Rebuild — Analiza P1–P4 + Plan Sprintów

> **Wersja:** v0.1.23 · 634 testów · 72% coverage · 3722 funkcji · 161 klas · CC̄ = 3.9
> **Źródła:** `SUMD.md`, struktura `rebuild/`, [TODO.md](TODO.md), [CHANGELOG.md](CHANGELOG.md), [docs/architecture.md](docs/architecture.md)
>
> Format wzorowany na analizie projektu Semcod GitHub App (`www`).
> Cel: zidentyfikować duplikacje, hotspoty, braki infrastruktury i testów oraz zaproponować realistyczną sekwencję sprintów.

---

## P1 · Refactoring — co i jak

### 1.1 `interfaces/cli.py` (561 LOC, 29 komend) — god-router

`walk()` ma **44 linie** i miesza 5 odpowiedzialności:

1. Definicja typer params (~15 args)
2. Ekstrakcja `ParameterSource` per param do `cli_overrides`
3. `ConfigLoader.load()` + merge z `cli_overrides`
4. Konstrukcja `Pipeline` / `AcceleratedPipeline`
5. `_fire_notifications()` na koniec

**Refactor:** wyodrębnij `WalkCLIArgs` (Pydantic) + `_build_walk_config(args)` + `_run_walk(config)`. CLI zostaje cienkim adapterem. Cel: `walk()` < 15 LOC, każda funkcja CC < 8.

To samo dla `dsl()` (36 LOC) i `accelerator()` (26 LOC).

### 1.2 Podwójna implementacja DSL

```@/home/tom/github/semcod/rebuild/rebuild/domain/dsl.py:1-9
"""
rebuild.dsl — Domain Specific Language for rebuild operations.
```

```@/home/tom/github/semcod/rebuild/rebuild/domain/dsl_v2.py:1-2
"""
rebuild DSL v2 — Pydantic-validated DSL with NLP support.
```

`dsl.py` (256 LOC, regex-based) + `dsl_v2.py` (455 LOC, Pydantic) — **dwie równoległe ścieżki dla tego samego problemu**. `dsl.py` używany przez `mvp_protocol.py:_handle_dsl` i `cli.py:dsl()`. `dsl_v2.py` używany w `interfaces/api/app.py:cmd_dsl`.

**Refactor:** zdeprecjonuj `dsl.py`, przepisz `mvp_protocol.py` i `cli.py` na `dsl_v2`. Oszczędność: ~256 LOC + jeden punkt prawdy.

**Alternatywa:** zastąp oba `testql` (PyPI v0.6.18) — pakiet już wymieniony w `pyproject.toml` jako `[full]`, ale niezaimportowany. Patrz [pyproject.toml:33](pyproject.toml).

### 1.3 `reporting/reporter.py` (452 LOC, 16 metod) — bóg-reporter

`_health_trend_by_day` (próg regresji) zdublowane w **3 miejscach**:

```@/home/tom/github/semcod/rebuild/rebuild/application/services/reporting/reporter.py:378
    def _health_trend_by_day(self, results_asc: List[DayResult], regression_threshold: float = 20.0) -> dict:
```

```@/home/tom/github/semcod/rebuild/rebuild/interfaces/commands/helpers.py:20
def compute_health_trend_labels(results: List[DayResult], regression_threshold: float = 20.0) -> List[str]:
```

```@/home/tom/github/semcod/rebuild/rebuild/application/services/notification_service.py:173
    def notify_health_regression(
```

**Refactor:** wyciągnij `application/services/regression_service.py` z jedną metodą `detect_regressions(results, threshold) -> Dict[day, RegressionEvent]`. Trzy miejsca wołają to samo. Później można zastąpić biblioteką `regres` (też w `[full]`).

### 1.4 Trio "fast mode" — nadmierna fragmentacja

Trzy duże pliki o pokrywającej się odpowiedzialności:

| Plik | LOC | Cel |
|------|-----|-----|
| `application/services/accelerator_deploy.py` | 451 | Deploy z worktree + DB snapshot |
| `application/accelerated_pipeline.py` | 432 | Pipeline orkiestrujący accelerator |
| `application/services/parallel_test_engine.py` | 450 | Async testowanie endpointów |

`accelerator_deploy.py` i `parallel_test_engine.py` mają niezależne `ThreadPoolExecutor` / `asyncio.gather` — można skonsolidować do `ConcurrencyExecutor` w `infrastructure/`.

### 1.5 Martwe pole `testql_passed`

```@/home/tom/github/semcod/rebuild/rebuild/domain/endpoint.py:47
    testql_passed: Optional[bool] = None
```

Pole nigdy nie jest zapisywane (zero przypisań w kodzie), tylko deserializowane i wyświetlane w TUI jako `—`. Albo wyciąć, albo wreszcie zintegrować `testql`.

---

## P2 · Infrastruktura — krytyczne braki

### 2.1 Brak `docker-compose.yml` dla samego rebuild

Mamy `Dockerfile` (66 LOC, multi-stage), ale żadnego compose-stacku. Użytkownik instaluje rebuild w kontenerze, ale **uruchomienie z dashboardem + persistent storage wyników** wymaga ręcznego skomponowania:

```yaml
# Brakuje: docker-compose.yml
services:
  rebuild:
    image: ghcr.io/semcod/rebuild:latest
    volumes:
      - ./repo:/workspace:ro
      - ./.rebuild:/results
    command: walk /workspace --output /results
  dashboard:
    image: ghcr.io/semcod/rebuild:latest
    command: serve --results-dir /results --port 7821
    ports: ["7821:7821"]
    volumes: ["./.rebuild:/results:ro"]
```

**Akcja:** dodać `docker-compose.example.yml` + `examples/04-docker-compose-deploy/`.

### 2.2 Dockerfile bez multi-arch

```@/home/tom/github/semcod/rebuild/Dockerfile:14
FROM python:${PYTHON_VERSION}-slim AS builder
```

Brak deklaracji `--platform=$BUILDPLATFORM` ani `linux/arm64` w `.github/workflows/docker.yml`. Krytyczne dla testowania na ARM (np. c2004 case). Dodaj `buildx` z `linux/amd64,linux/arm64`.

### 2.3 Brak `.pre-commit-config.yaml`

Repozytorium ma `ruff` + `mypy` w `pyproject.toml`, ale żaden hook nie wymusza ich lokalnie. Każdy commit może wprowadzić formatting/lint debt.

**Akcja:** `.pre-commit-config.yaml` z `ruff format`, `ruff check --fix`, `mypy rebuild/`.

### 2.4 `mypy` w `pyproject.toml` ale nie w CI

```toml
[tool.mypy]
python_version = "3.10"
strict = false
ignore_missing_imports = true
```

Konfiguracja istnieje, ale `.github/workflows/ci.yml` jej nie wywołuje. Strict=false + brak gating = mypy istnieje tylko na papierze.

**Akcja:** dodać krok `mypy rebuild/ --strict` w `ci.yml` (najpierw non-blocking, potem blocking).

### 2.5 Brak macierzy Python w CI

W `pyproject.toml` deklarujemy support dla Python 3.10/3.11/3.12, ale CI najprawdopodobniej testuje tylko jedną wersję. To miny czekają na release.

**Akcja:** matrix `python-version: ["3.11", "3.12"]` w `ci.yml`.

### 2.6 Brak `release-please` / semantic-release

Mamy `scripts/bump_version.py` + `auto_bump.yml`, ale:
- changelog jest pisany ręcznie (`docs/` updates v0.1.23)
- brak automatycznych tag-release-asset z conventional commits

**Akcja:** rozważ migrację na `release-please-action` lub `semantic-release` (Node) — jeden YAML eliminuje 2 skrypty.

---

## P3 · Brakujące funkcjonalności — co wdrożyć

Hierarchia wpływu na **adopcję** projektu (rebuild jest narzędziem dev — sukces = stars/installs, nie revenue):

### 3.1 c2004 Full 30-day Walk (P17 #1) — **bloker case-study**

Phase 15 zatrzymał się na 1-dniowym walk z `--deploy none`. Bez 30-day pełnego walk (`--deploy docker-compose`) case-study w README jest niedopowiedziany. To bloker dla materiału marketingowego (blog post / Show HN).

**Akcja:** dedykowany skrypt `scripts/run_c2004_full.sh` + raport w `docs/case_study_c2004.md`.

### 3.2 Performance profiling (P17 #2)

> *"Profilowanie walk na dużych repo (>500 commitów) — targetowane <5min/commit"*

Brak benchmarków = brak SLO. Bez tego użytkownicy zniechęcą się przy pierwszym dużym repo.

**Akcja:** `scripts/benchmark_walk.py` + `docs/benchmarks.md` z tabelą per-repo-size.

### 3.3 `rebuild watch` — long-running mode

Dziś `walk` to one-shot. Brak trybu *"obserwuj nowe commity i triggeruj walk"* (domena biblioteki `wup`, też zakomentowana w `pyproject.toml`).

**Akcja:** `rebuild watch /repo --interval 300` + `notification_service.notify_walk_completed()`.

### 3.4 Diff-aware scanning (P17 #5)

Endpoint scanner przebiega **cały** kod per commit. Przy 100 commitach to 100× pełny skan. Cache + diff (`git diff prev_sha --name-only` → tylko zmienione pliki) skróci walk 5–10×.

**Akcja:** `EndpointScanner.scan(diff_only=True, prev_sha=...)`.

### 3.5 CI integration recipes

```
examples/
  ├── .github/workflows/rebuild.yml      # ← brakuje
  ├── .gitlab-ci.yml                     # ← brakuje
  └── .circleci/config.yml               # ← brakuje
```

Bez gotowych recepty użytkownik musi wymyślać integrację od zera. To friction → niska adopcja.

**Akcja:** `examples/05-ci-integrations/` z 3 plikami YAML.

### 3.6 Web Dashboard (React) — opcjonalnie

Aktualne `serve` to statyczny HTML + SSE. Phase 17 wzmiankuje React/Next.js dashboard. **Niska priorytet** — duża praca, dwukrotne CI, mało zwrotu vs poprawa istniejącego dashboardu.

### 3.7 Grafana / Prometheus exporter — niski priorytet

`metrics.py` exportujący `health_pct{repo,commit}` jako Prometheus text format. Ułatwi dashboardy w istniejącym Grafanie. Niewielki wysiłek (~50 LOC), pełne wsparcie ekosystemu.

---

## P4 · Testy — gaps i co naprawić

### 4.1 Coverage 72%, target 80% — gap 8 punktów

```
634 testów passing, 72% coverage
```

Niepokryte (z poprzedniej analizy): edge-cases w `pipeline.py`, `accelerated_pipeline.py`, `interfaces/api/app.py`, `interfaces/dashboard.py` (HTML rendering).

**Akcja:** `tests/test_api_endpoints.py` (FastAPI TestClient), `tests/test_dashboard_render.py` (snapshot HTML).

### 4.2 Brak gating coverage w CI

`ci.yml` najprawdopodobniej liczy coverage, ale nie odrzuca PR przy spadku. Dodaj `--cov-fail-under=70` (próg minimalny, niżej niż obecny stan = bezpieczna sieć).

### 4.3 Brak mutation testing

`pytest --cov` mówi *"linia wykonana"*, ale nie *"asercja działa"*. `mutmut` lub `cosmic-ray` na `domain/` (czyste, bez side-effectów) potwierdziłby jakość testów.

**Akcja:** `make mutate` na `rebuild/domain/` w nightly CI.

### 4.4 Brak testów integracyjnych dla obu DSL

`tests/test_dsl.py` (jeśli istnieje) testuje albo `dsl.py`, albo `dsl_v2.py`, ale nie jeden i drugi przez wspólny adapter. Konsekwencja: refactor (P1.2) może coś zepsuć niezauważalnie.

**Akcja:** `tests/test_dsl_compat.py` z parametrycznymi przypadkami: `assert dsl_v1.parse(s) ≈ dsl_v2.parse(s)`.

### 4.5 Brak end-to-end test harness

Mamy unit testy, ale brak `tests/e2e/` z prawdziwym docker-compose mini-projektu (np. `examples/02-docker-compose-project`) i pełnym `walk`. Ten typ testów wykryje regresje deploy/scan/test, których unit testy nie złapią.

**Akcja:** `tests/e2e/test_full_walk.py` z fixturem `tmp_compose_project` i 1-dniowym walk.

### 4.6 Brak docs lint

`docs/` ma 13 plików .md z linkami między sobą. Jeden zły link i nawigacja MkDocs się rozsypie. Brak `markdown-link-check` w CI.

**Akcja:** `mkdocs build --strict` w `.github/workflows/docs.yml` — fail przy pierwszym broken link.

---

## Sekwencja rekomendowana — Plan Sprintów

### Sprint 1 (tydzień 1–2) — Quality Gates + Infra Foundation

Ryzyko niskie, zwrot wysoki: gating + multi-arch image.

- [ ] **Pre-commit hooks** (`.pre-commit-config.yaml` z ruff + mypy)
- [ ] **CI matrix** Python 3.11/3.12 w [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- [ ] **Coverage gate** `--cov-fail-under=70`
- [ ] **mypy w CI** (non-blocking → blocking po fix)
- [ ] **Dockerfile multi-arch** (`linux/amd64,linux/arm64` w `docker.yml`)
- [ ] **mkdocs build --strict** w `docs.yml`
- [ ] **docker-compose.example.yml** w roocie

### Sprint 2 (tydzień 3–4) — Konsolidacja Duplikatów

Refactory niskiego ryzyka, czyszczą long-tail TODO.

- [ ] **Wyciąg `regression_service.py`** — eliminuje 3 duplikaty health-trend
- [ ] **Deprecation `dsl.py`** — przepisz `cli.py:dsl()` i `mvp_protocol.py:_handle_dsl` na `dsl_v2`
- [ ] **Refactor `cli.py:walk()`** — wyodrębnij `_build_walk_config(args)` + `_run_walk(config)`
- [ ] Usuń lub ożyw `Endpoint.testql_passed`
- [ ] [TODO Phase 17] **Diff-aware scanning** (cache na `git diff`)

### Sprint 3 (tydzień 5–6) — Showcase + Performance

Materiały marketingowe + dowód wydajności.

- [ ] **c2004 Full 30-day Walk** (`scripts/run_c2004_full.sh` + raport)
- [ ] **`scripts/benchmark_walk.py`** + `docs/benchmarks.md`
- [ ] **CI integration recipes** w `examples/05-ci-integrations/`
- [ ] **Coverage ≥80%** (Phase 17 #3)
- [ ] **E2E test harness** `tests/e2e/test_full_walk.py`

### Sprint 4 (tydzień 7–8) — Reuse Bibliotek + Watch Mode

Wreszcie używamy `[full]` extras.

- [ ] **`testql` integracja** — zastąp `dsl.py` + `dsl_v2.py` (lub przynajmniej jeden)
- [ ] **`regres` integracja** — zastąp `regression_service.py` (Sprint 2) wywołaniami regres
- [ ] **`wup` integracja → `rebuild watch`** — long-running mode
- [ ] **Mutation testing** (`mutmut` na `rebuild/domain/`)

### Sprint 5+ — Ecosystem Extensions

Niska priorytet, jednorazowe inwestycje.

- [ ] **Grafana / Prometheus exporter** (`/metrics` endpoint)
- [ ] **Refactor `reporter.py`** — split na `health_reporter.py`, `chart_reporter.py`, `summary_reporter.py`
- [ ] **VS Code extension** (Phase 17)
- [ ] **Web Dashboard (React)** — tylko jeśli prawdziwa potrzeba użytkowników
- [ ] **`release-please` migracja** ze `scripts/bump_version.py`

---

## Najważniejsze obserwacje

1. **Projekt ma solidną architekturę warstwową** (interfaces / application / domain / infrastructure / intelligence) i dobre pokrycie testami (72%, 634 testy).
2. **Główny dług techniczny:** trzy obszary duplikacji (DSL × 2, regression × 3, fast-mode × 3).
3. **Główny dług infrastruktury:** brak multi-arch image, brak pre-commit, brak mypy w CI, brak coverage gate.
4. **Główny dług dowodowy:** c2004 case-study niezakończony (1 dzień zamiast 30); brak benchmarków.
5. **Ironia:** projekt importuje `costs`, `goal`, `pfix` (sibling libs), ale **nie** importuje `wup`, `regres`, `testql` które sam by reimplementował. Sprint 4 to długoterminowa dieta DRY.

Pierwszy sprint nie wymaga żadnych zmian w architekturze ani decyzji produktowych — to czyste hardening. **Najtańszy zwrot: pre-commit + multi-arch Dockerfile + coverage gate w jeden dzień.**

---

*Linki:*
- [README](README.md) · [TODO.md](TODO.md) · [CHANGELOG.md](CHANGELOG.md)
- [docs/architecture.md](docs/architecture.md) · [docs/usage.md](docs/usage.md)
- [docs/case_study_c2004.md](docs/case_study_c2004.md) · [docs/c2004.md](docs/c2004.md)
- [pyproject.toml](pyproject.toml) · [Dockerfile](Dockerfile) · [mkdocs.yml](mkdocs.yml)
