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
- [ ] **D3.js Enhancements**: Add "Code Evolution" playback to the graph (watch dependencies change over time).
- [ ] **TUI Refactor**: Finalize extraction of domain logic from `interfaces/tui.py`.
