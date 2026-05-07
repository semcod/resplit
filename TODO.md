# TODO: rebuild Roadmap

> **Current version:** v0.1.23 · **Tests:** 634 · **Coverage:** 72%
>
> See also: [README](README.md) · [Changelog](CHANGELOG.md) · [Architecture](docs/architecture.md) · [Usage Guide](docs/usage.md)

---

## Phase 10: c2004 Testing & Improvements ✅

### ✅ Zrobione (sesja 2026-05-01)
- [x] **Clone for walk**: Pipeline klonuje repo do `.rebuild/repo/` — oryginał nienaruszony
- [x] **git checkout --force**: Bezpieczne przełączanie commitów w klonie
- [x] **Replay mode fix**: `start()` w replay tylko sprawdza health, nie uruchamia nowego compose
- [x] **Replay reload**: `docker restart <name>` bezpośrednio po nazwie kontenera
- [x] **history_service**: Obsługa nowego formatu `results.json` (dict z kluczem `results`)
- [x] **index.html**: Eksport JSON/YAML/TOON + toolbar w nawigacji
- [x] **rebuild serve**: Komenda do serwowania raportów na HTTP
- [x] **Deploy Log Details**: Store full docker logs in `DayResult` and show them in reports when deploy fails.
- [x] **Param Substitution**: In OpenAPI/FastAPI scanner — replace `{param}` with test values from `rebuild.yaml`.
- [x] **Fixture Seed**: Support `test_fixtures:` in `rebuild.yaml`.
- [x] **Auth Config**: Add `auth:` to `rebuild.yaml` for custom headers (Bearer tokens, etc).

### 🔴 Krytyczne
- [x] **Replay + volume mount**: W replay mode Docker używa aktualnego obrazu, nie kodu z checkoutu. Rozwiązanie: w clone podmontować katalog kodu jako volume lub budować obraz per commit.
- [x] **init tworzy rebuild.yaml w oryginalnym repo**: `init()` wywołany z `walk` tworzy pliki w `repo_path`. Powinno trafiać do klona lub być pomijane.
- [x] **Deploy Retry**: Dodać mechanizm retry z backoff dla niestabilnych deployów.
- [x] **Health Check Verbose**: Pokaż szczegółowy log health-check (curl output) gdy serwis nie odpowiada.
- [x] **Manual Override**: Support a `patch/` directory in `.rebuild/` to automatically apply fixes to the cloned repo before walk.
- [x] **Health Recovery**: If a day fails, allow manual "fix" commit in the clone to see if health improves (without modifying source).
- [x] **Token Propagation**: Zaloguj się raz przed testem, propaguj token Bearer do wszystkich requestów.
- [x] **Per-Endpoint Body**: Opcjonalne `body:` dla POST/PUT/PATCH w konfiguracji testów.

### 🟡 Średnie — Raporty c2004
- [x] **Failure Grouping**: W raporcie HTML grupuj błędy wg kategorii (auth, template, missing).
- [x] **Trend Chart**: Wykres trendu health% w czasie (Chart.js / SVG inline).
- [x] **Endpoint Diff**: Pokaż endpointy które znikły lub pojawiły się między commitami.
- [x] **Response Time Tracking**: Zmierz i wyświetl `time_ms` dla wszystkich requestów.

### 🟢 Niskie — Analyze na c2004
- [x] Uruchomić `rebuild analyze duplicates` na c2004 i zapisać wyniki.
- [x] Uruchomić `rebuild analyze services` na c2004 i zapisać wyniki.
- [x] Uruchomić `rebuild analyze truth` na wybrane moduły c2004.


## Phase 11: Deep Semantic Analysis ✅
- [x] **Semantic Embeddings**: Integrate `sentence-transformers` for conceptual similarity detection in `duplication_engine`. → [Analyze docs](docs/guide/analyze.md#vector-search)
- [x] **Vector Search**: Store code fragments in a vector database for rapid semantic lookup across large repos. → [CLI: vector-build/vector-query](docs/reference/cli.md#rebuild-analyze-vector-build-path)

## Phase 12: Real-time & Cross-Repo ✅
- [x] **Multi-Repo Support**: Analyze dependencies and clones across multiple repositories. → [Analyze: multi-repo](docs/guide/analyze.md#multi-repo)
- [x] **Real-time Monitoring**: Show live analysis results and event logs in the dashboard. → [Visualization](docs/usage.md#6-visualization)
- [x] **Auto-PR Agent**: Automatically open PRs on GitHub/GitLab using generated AI summaries. → [Auto-PR docs](docs/guide/auto-pr.md)

## Phase 13: UI/UX Refinement ✅
- [x] **D3.js Enhancements**: Add "Code Evolution" playback to the graph (watch dependencies change over time). → [Architecture: evolution_viz](docs/architecture.md)
- [x] **TUI Refactor**: Finalize extraction of domain logic from `interfaces/tui.py`. → [CLI: tui](docs/reference/cli.md)

---

## Phase 14: Production Readiness ✅ (ukończone 2026-05-01)

### ✅ Zrobione
- [x] **Test Coverage ≥60%**: 347 testów passing, 60% pokrycie (`pytest --cov`)
- [x] **--health-timeout CLI**: Nowa opcja `--health-timeout` w `rebuild walk` → [CLI Reference](docs/reference/cli.md#rebuild-walk)
- [x] **Deploy Error Classification**: Auto-klasyfikacja błędów → [Architecture: Deploy Error](docs/architecture.md#deploy-error-classification)
- [x] **Documentation Update**: Zaktualizowane `docs/usage.md`, `docs/architecture.md`, `README.md`
- [x] **Service Table in Docs**: Kompletna tabela usług → [Architecture: Key Services](docs/architecture.md#key-services)

---

## Phase 15: c2004 Integration & Stability ✅

### 🔴 Krytyczne
- [x] **c2004 npm ci fix**: Napraw `identification-frontend` Dockerfile — `npm ci` failuje przez brak `package-lock.json` lub niekompatybilne zależności. Zablokowane: `--deploy docker-compose` nie może zakończyć buildu. (Fixed: changed to `if [ -f package-lock.json ]; then npm ci; else npm install; fi`)
- [x] **c2004 Walk z --deploy none**: Uruchomić pełny `rebuild walk` c2004 z `--deploy none` (stack już działa) i zmapować 444 endpointów historycznie przez 30 dni. (Completed: ran 1-day test walk, found 442 endpoints, generated timeline/dashboard)
- [x] **Config Validation**: JSON Schema dla `rebuild.yaml` z walidacją przy starcie — lepsze komunikaty błędów zamiast traceback.
- [x] **PipelineEvent Import Fix**: Napraw `ImportError: cannot import name 'PipelineEvent' from 'rebuild.domain.events'` — przeniesiono `PipelineEvent` do `domain_events.py` jako legacy class, dodano do `__init__.py`, usunięto zbędne importy z `pipeline.py` i `accelerated_pipeline.py`.

### 🟠 Wysokie
- [x] **Walk Result Regression Guard**: Automatyczny test regresji — jeśli `health_%` spada o >20% vs poprzedni dzień, flag to w raporcie.
- [x] **c2004 Dashboard**: Uruchomić `rebuild serve` na wynikach c2004 i sprawdzić poprawność dashboardu dla 444 endpointów.
- [x] **`--output` default respects rebuild.yaml**: Gdy `output.dir` jest w `rebuild.yaml`, powinno nadpisywać domyślne `.rebuild` bez potrzeby flagi CLI.

### 🟡 Średnie
- [x] **Deploy log truncation**: Logi `docker compose` mogą być >1MB w `results.json`. Dodać limit (np. ostatnie 200 linii) z informacją o obcięciu.
- [x] **Health verbose summary**: Gdy health check failuje, wyświetlić skrót odpowiedzi HTTP (status + pierwsze 200 bajtów body).
- [x] **Endpoint count diff warning**: Jeśli liczba endpointów zmienia się o >10% między dniami, wyświetlić ostrzeżenie w tabeli.

---

## Phase 16: Production Release ✅

### 🔴 Krytyczne
- [x] **PyPI Package**: Publikacja `rebuild` na PyPI — build+twine PASSED v0.1.20 → [PyPI](https://pypi.org/project/rebuild/)
- [x] **CI/CD Pipeline**: GitHub Actions — testy, linting, coverage gate ≥70% → [`.github/workflows/`](.github/workflows/)
- [x] **Semantic Versioning**: Automatyczny bump — `scripts/bump_version.py`

### 🟠 Wysokie
- [x] **Docker Image**: `ghcr.io/semcod/rebuild:latest` — Dockerfile + `.github/workflows/docker.yml`
- [x] **Config Validation**: Pydantic-based → [Config Reference](docs/reference/config.md) · [Configuration](docs/getting-started/configuration.md#validation)
- [x] **Plugin System**: Entry points — `rebuild/plugins/` → [Plugin docs](docs/guide/plugins.md)
- [x] **Documentation Site**: MkDocs Material → [GitHub Pages](https://semcod.github.io/resplit)

### 🟡 Średnie
- [x] **TUI Full Features**: j/k navigation, g/G, live log, endpoint browser
- [x] **Export Formats**: CSV, Markdown summary
- [x] **Notification Hooks**: Slack/Discord webhooks → [Config Reference](docs/reference/config.md)
- [x] **Snapshot Management**: LRU cache, auto-prune
- [x] **Test Coverage ≥70%**: osiągnięto 72% (634 testów)

---

## Phase 17: Next Steps (PLANNED)

### 🔴 Krytyczne
- [ ] **c2004 Full Walk (30 days)**: Uruchomić `rebuild walk` z `--deploy docker-compose --days 30` na c2004
- [ ] **Performance Profiling**: Profilowanie walk na dużych repo (>500 commitów) — targetowane <5min/commit
- [ ] **Test Coverage ≥80%**: Następny milestone — przetestować pozostałe edge cases w pipeline/services

### 🟠 Wysokie
- [ ] **TestQL Integration**: Natywna integracja z `testql` DSL dla zaawansowanych scenariuszy testowych
- [ ] **Diff-aware Scanning**: Skanowanie tylko zmienionych endpointów (zamiast pełnego skanu)
- [ ] **Report Templates**: Konfigurowalne szablony raportów HTML (Jinja2)

### 🟡 Średnie
- [ ] **Web Dashboard**: Standalone web UI (React/Next.js) z real-time SSE
- [ ] **Grafana Integration**: Eksport metryk health% do Prometheus/Grafana
- [ ] **VS Code Extension**: Wyświetlanie wyników rebuild w edytorze
