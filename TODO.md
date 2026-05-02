# TODO: rebuild Roadmap

## Phase 10: c2004 Testing & Improvements (AKTYWNY)

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


## Phase 11: Deep Semantic Analysis
- [x] **Semantic Embeddings**: Integrate `sentence-transformers` for conceptual similarity detection in `duplication_engine`.
- [x] **Vector Search**: Store code fragments in a vector database for rapid semantic lookup across large repos.

## Phase 12: Real-time & Cross-Repo
- [x] **Multi-Repo Support**: Analyze dependencies and clones across multiple repositories.
- [x] **Real-time Monitoring**: Show live analysis results and event logs in the dashboard.
- [x] **Auto-PR Agent**: Automatically open PRs on GitHub/GitLab using generated AI summaries.

## Phase 13: UI/UX Refinement
- [x] **D3.js Enhancements**: Add "Code Evolution" playback to the graph (watch dependencies change over time).
- [x] **TUI Refactor**: Finalize extraction of domain logic from `interfaces/tui.py`.

---

## Phase 14: Production Readiness ✅ (ukończone 2026-05-01)

### ✅ Zrobione
- [x] **Test Coverage ≥60%**: 347 testów passing, 60% pokrycie (`pytest --cov`)
- [x] **--health-timeout CLI**: Nowa opcja `--health-timeout` w `rebuild walk` dla dużych stacków (np. c2004 ARM64 ~300s)
- [x] **Deploy Error Classification**: Auto-klasyfikacja błędów: `compose_build_fail`, `port_conflict`, `migration_fail`, `missing_env`
- [x] **Documentation Update**: Zaktualizowane `docs/usage.md`, `docs/architecture.md`, `README.md`
- [x] **Service Table in Docs**: Kompletna tabela usług w architekturze

---

## Phase 15: c2004 Integration & Stability (AKTYWNY)

### 🔴 Krytyczne
- [ ] **c2004 npm ci fix**: Napraw `identification-frontend` Dockerfile — `npm ci` failuje przez brak `package-lock.json` lub niekompatybilne zależności. Zablokowane: `--deploy docker-compose` nie może zakończyć buildu.
- [ ] **c2004 Walk z --deploy none**: Uruchomić pełny `rebuild walk` c2004 z `--deploy none` (stack już działa) i zmapować 444 endpointów historycznie przez 30 dni.
- [x] **Config Validation**: JSON Schema dla `rebuild.yaml` z walidacją przy starcie — lepsze komunikaty błędów zamiast traceback.

### 🟠 Wysokie
- [x] **Walk Result Regression Guard**: Automatyczny test regresji — jeśli `health_%` spada o >20% vs poprzedni dzień, flag to w raporcie.
- [x] **c2004 Dashboard**: Uruchomić `rebuild serve` na wynikach c2004 i sprawdzić poprawność dashboardu dla 444 endpointów.
- [x] **`--output` default respects rebuild.yaml**: Gdy `output.dir` jest w `rebuild.yaml`, powinno nadpisywać domyślne `.rebuild` bez potrzeby flagi CLI.

### 🟡 Średnie
- [x] **Deploy log truncation**: Logi `docker compose` mogą być >1MB w `results.json`. Dodać limit (np. ostatnie 200 linii) z informacją o obcięciu.
- [x] **Health verbose summary**: Gdy health check failuje, wyświetlić skrót odpowiedzi HTTP (status + pierwsze 200 bajtów body).
- [x] **Endpoint count diff warning**: Jeśli liczba endpointów zmienia się o >10% między dniami, wyświetlić ostrzeżenie w tabeli.

---

## Phase 16: Production Release

### 🔴 Krytyczne
- [ ] **PyPI Package**: Publikacja `rebuild` na PyPI z poprawnymi metadata i `python_requires`
- [ ] **CI/CD Pipeline**: GitHub Actions — testy, linting (`ruff`), coverage gate ≥60%, publish on tag
- [ ] **Semantic Versioning**: Automatyczny bump z `CHANGELOG.md` przy każdym merge

### 🟠 Wysokie
- [ ] **Docker Image**: Oficjalny obraz `ghcr.io/semcod/rebuild:latest` z CLI i Playwright
- [ ] **Config Validation**: `pydantic`-based validation dla `rebuild.yaml` z czytelnym komunikatem błędu
- [ ] **Plugin System**: Extensible scanners i reporters przez entry points
- [ ] **Documentation Site**: MkDocs z Material theme — hosted na GitHub Pages

### 🟡 Średnie
- [ ] **TUI Full Features**: Nawigacja klawiaturą, live log view, endpoint browser
- [ ] **Export Formats**: CSV, Markdown summary raport
- [ ] **Notification Hooks**: Webhook (Slack/Discord) przy deploy fail lub health regresji
- [ ] **Snapshot Management**: LRU cache dla DB snapshotów — auto-prune starych
- [ ] **Test Coverage ≥70%**: Kolejny milestone po aktualnym 60%
