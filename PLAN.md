# rebuild — Plan paczki

## Cel

Nowa paczka `rebuild` łączy `deta` + `wup` + `regres` + `testql`, aby:

1. **Przejść wstecz** po historii git projekt po dniu
2. Dla każdego dnia: znaleźć najwcześniejszy commit, wykonać deploy
3. **Przetestować** wszystkie endpointy przez `testql`
4. **Zapisać** zrzuty ekranu (Playwright) + listę endpointów jako HTML
5. **Zorganizować** wyniki w folderach `YYYY-MM-DD/`
6. **Przywrócić** konkretny endpoint (gdy działał) jako izolowany projekt

---

## Przepływ główny

```
rebuild walk <repo> [--from DATE] [--to DATE] [--deploy docker-compose]

  Dla każdego dnia w przedziale:
    1. git log --before=DATE --after=DATE-1d  → najwcześniejszy commit
    2. git checkout <commit>
    3. deta scan .  → wykryj usługi, porty, endpointy
    4. deploy (docker-compose up -d / uvicorn / ...) + health wait
    5. testql scenarios/ --url http://... → testy endpointów
    6. Playwright screenshot każdego endpointu (screenshotter.py)
    7. Zapisz raport HTML + JSON w .rebuild/YYYY-MM-DD/
    8. docker-compose down / cleanup

rebuild restore <endpoint-path> [--date YYYY-MM-DD]
  → wyodrębnij działający endpoint jako projekt:
    /endpoint-path/
      frontend/
      backend/
      docker/
      README.md
```

---

## Architektura paczki

```
rebuild/
├── rebuild/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI: walk, restore, report, version
│   ├── git_walker.py       # Iteracja po historii git dzień po dniu
│   ├── deployer.py         # Detekcja metody deploy + uruchomienie
│   ├── endpoint_scanner.py # deta scan → lista endpointów
│   ├── tester.py           # testql runner dla każdego endpointu
│   ├── screenshotter.py    # Playwright → PNG per endpoint (retry/timeout)
│   ├── reporter.py         # HTML raport + JSON artefakt per dzień
│   ├── restorer.py         # Wyodrębnij endpoint z historii git
│   ├── dashboard.py        # Timeline CC + health% porównawczy
│   └── models.py           # Dataclassy: DayResult, EndpointResult, ...
├── tests/
│   ├── test_models.py
│   ├── test_git_walker.py
│   ├── test_deployer.py
│   ├── test_endpoint_scanner.py
│   ├── test_reporter.py
│   ├── test_restorer.py
│   ├── test_tester.py
│   └── test_screenshotter.py
├── examples/
│   ├── walk_dry_run.sh
│   ├── restore_endpoint.sh
│   └── rebuild.yaml
├── pyproject.toml
├── README.md
└── rebuild.yaml.example
```

---

## Integracja z istniejącymi paczkami

| Moduł rebuild      | Używa z               | Do czego |
|--------------------|-----------------------|----------|
| `endpoint_scanner` | `deta scan`           | Wykrywa usługi, porty, endpointy z docker-compose/OpenAPI |
| `tester`           | `testql`              | Uruchamia testy na wykrytych endpointach |
| `screenshotter`    | Playwright (opcjonalnie) | Screenshot per URL z retry/timeout |
| `git_walker`       | `regres` (opcjonalnie) | Historia CC/duplikacji obok deployów |
| `deployer`         | `wup` (health check)  | Sprawdzenie czy usługa żyje po deploy |
| `dashboard`        | `regres` / `toon`     | CC z plików nałożony na timeline health% |

---

## Format wyjścia per dzień

```
.rebuild/
  2024-01-15/
    commit.txt              # sha + message najwcześniejszego commitu
    endpoints.json          # lista endpointów wykryta przez deta
    results.json            # wyniki HTTP probe + testql per endpoint
    testql-results.json     # surowe wyniki testql (jeśli dostępny)
    report.html             # pełny raport HTML z osadzonymi screenshotami
    screenshots/
      GET_api_health.png
      GET_api_repos.png
      POST_api_audit.png
  index.html                # zbiorczy timeline wszystkich dni
```

---

## Fazy implementacji

### Faza 0 — Szkielet ✓
- [x] `pyproject.toml` — name=rebuild
- [x] `models.py` — dataklasy (WalkConfig, DayResult, Endpoint, CommitInfo)
- [x] `git_walker.py` — iteracja po historii
- [x] `deployer.py` — detekcja + uruchomienie docker-compose/uvicorn
- [x] `cli.py` — `rebuild walk`, `rebuild restore`, `rebuild report`, `rebuild version`
- [x] `tests/` — test_models, test_git_walker, test_deployer (podstawowe)

### Faza 1 — Testy endpointów ← w toku
- [x] `endpoint_scanner.py` — deta scan + OpenAPI + Traefik labels fallback
- [x] `reporter.py` — HTML + JSON raport per dzień + timeline index
- [x] `restorer.py` — wyodrębnij endpoint jako izolowany projekt
- [x] `tests/test_endpoint_scanner.py`
- [x] `tests/test_reporter.py`
- [x] `tests/test_restorer.py`
- [x] `tester.py` — wywołanie `testql` i parsowanie wyników
- [x] `screenshotter.py` — Playwright screenshots z retry/timeout
- [x] `tests/test_tester.py`
- [x] `tests/test_screenshotter.py`
- [x] podłączyć `tester` + `screenshotter` do `cli.py walk`

### Faza 2 — Przykłady i docs
- [x] `examples/walk_dry_run.sh`
- [x] `examples/restore_endpoint.sh`
- [x] `examples/rebuild.yaml`
- [ ] `README.md` — pełna dokumentacja

### Faza 3 — Zaawansowane
- [x] `dashboard.py` — timeline CC (toon plików) nałożony na health%
- [x] Auto-detect "ostatni działający dzień" per endpoint (restorer)
- [x] `cli.py dashboard` — nowa komenda
- [ ] Integracja z `regres doctor` dla analizy przyczyn regresji

---

## Przykłady użycia

```bash
# Przejdź ostatnie 30 dni
rebuild walk . --days 30

# Konkretny zakres
rebuild walk /home/tom/github/oqlos/www --from 2024-01-01 --to 2024-04-01

# Przywróć endpoint /api/health z ostatniego działającego dnia
rebuild restore /api/health --output ./restored/api-health

# Wygeneruj zbiorczy raport z istniejących wyników
rebuild report

# Tylko skanuj bez deploy (dry-run)
rebuild walk . --dry-run

# Pokaż wersję
rebuild version
```

---

## rebuild.yaml — konfiguracja projektu

```yaml
project:
  name: "semcod"
  repo: "."

deploy:
  method: docker-compose          # docker-compose | uvicorn | custom | none
  compose_file: docker-compose.yml
  health_url: http://localhost:8003/api/health
  health_timeout: 60
  health_interval: 2

scan:
  days: 30                        # ile dni wstecz
  earliest_commit_per_day: true   # najwcześniejszy commit per dzień

testql:
  scenarios_dir: scenarios/
  base_url: http://localhost:8003
  timeout: 10

output:
  dir: .rebuild
  screenshots: true
  html_report: true
```
