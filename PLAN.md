# retrodep — Plan paczki

## Cel

Nowa paczka `retrodep` łączy `deta` + `wup` + `regres` + `testql`, aby:

1. **Przejść wstecz** po historii git projekt po dniu
2. Dla każdego dnia: znaleźć najwcześniejszy commit, wykonać deploy
3. **Przetestować** wszystkie endpointy przez `testql`
4. **Zapisać** zrzuty ekranu (Playwright) + listę endpointów jako HTML
5. **Zorganizować** wyniki w folderach `YYYY-MM-DD/`
6. **Przywrócić** konkretny endpoint (gdy działał) jako izolowany projekt

---

## Przepływ główny

```
retrodep walk <repo> [--from DATE] [--to DATE] [--deploy docker-compose]

  Dla każdego dnia w przedziale:
    1. git log --before=DATE --after=DATE-1d  → najwcześniejszy commit
    2. git checkout <commit>
    3. deta scan .  → wykryj usługi, porty, endpointy
    4. deploy (docker-compose up -d / uvicorn / ...) + health wait
    5. testql scenarios/ --url http://... → testy endpointów
    6. Playwright screenshot każdego endpointu
    7. Zapisz raport HTML + JSON w .retrodep/YYYY-MM-DD/
    8. docker-compose down / cleanup

retrodep restore <endpoint-path> [--date YYYY-MM-DD]
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
retrodep/
├── retrodep/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI: walk, restore, report, status
│   ├── git_walker.py       # Iteracja po historii git dzień po dniu
│   ├── deployer.py         # Detekcja metody deploy + uruchomienie
│   ├── endpoint_scanner.py # deta scan → lista endpointów
│   ├── tester.py           # testql runner dla każdego endpointu
│   ├── screenshotter.py    # Playwright → PNG per endpoint
│   ├── reporter.py         # HTML raport + JSON artefakt per dzień
│   ├── restorer.py         # Wyodrębnij endpoint z historii git
│   └── models.py           # Dataclassy: DayResult, EndpointResult, ...
├── tests/
│   ├── test_git_walker.py
│   ├── test_deployer.py
│   └── test_reporter.py
├── pyproject.toml
├── README.md
└── retrodep.yaml.example   # Konfiguracja projektu
```

---

## Integracja z istniejącymi paczkami

| Moduł retrodep     | Używa z             | Do czego |
|--------------------|---------------------|----------|
| `endpoint_scanner` | `deta scan`         | Wykrywa usługi, porty, endpointy z docker-compose/OpenAPI |
| `tester`           | `testql`            | Uruchamia testy na wykrytych endpointach |
| `screenshotter`    | Playwright (z testql) | Screenshot per URL |
| `git_walker`       | `regres` (opcjonalnie) | Historia CC/duplikacji obok deployów |
| `deployer`         | `wup` (health check) | Sprawdzenie czy usługa żyje po deploy |

---

## Format wyjścia per dzień

```
.retrodep/
  2024-01-15/
    commit.txt          # sha + message najwcześniejszego commitu
    endpoints.json      # lista endpointów wykryta przez deta
    testql-results.json # wyniki testql per endpoint
    report.html         # pełny raport HTML z osadzonymi screenshotami
    screenshots/
      GET_api_health.png
      GET_api_repos.png
      POST_api_audit.png
```

---

## Fazy implementacji

### Faza 0 — Szkielet (to build now)
- [x] `pyproject.toml`
- [x] `models.py` — dataklasy
- [x] `git_walker.py` — iteracja po historii
- [x] `deployer.py` — detekcja + uruchomienie docker-compose
- [x] `cli.py` — `retrodep walk`, `retrodep restore`, `retrodep report`

### Faza 1 — Testy endpointów
- [ ] `endpoint_scanner.py` — integracja z `deta`
- [ ] `tester.py` — wywołanie `testql` i parsowanie wyników
- [ ] `screenshotter.py` — Playwright screenshots

### Faza 2 — Raporty i przywracanie
- [ ] `reporter.py` — HTML + JSON raport per dzień
- [ ] `restorer.py` — wyodrębnij endpoint jako izolowany projekt

### Faza 3 — Zaawansowane
- [ ] Dashboard porównawczy (timeline CC + wyniki testów)
- [ ] Auto-detect "ostatni działający dzień" per endpoint
- [ ] Integracja z `regres doctor` dla analizy przyczyn regresji

---

## Przykłady użycia

```bash
# Przejdź ostatnie 30 dni
retrodep walk . --days 30

# Konkretny zakres
retrodep walk /home/tom/github/oqlos/www --from 2024-01-01 --to 2024-04-01

# Przywróć endpoint /api/health z ostatniego działającego dnia
retrodep restore /api/health --output ./restored/api-health

# Pokaż timeline wszystkich endpointów
retrodep report --format html --out timeline.html

# Tylko skanuj bez deploy (dry-run)
retrodep walk . --dry-run
```

---

## retrodep.yaml — konfiguracja projektu

```yaml
project:
  name: "semcod"
  repo: "."
  
deploy:
  method: docker-compose          # docker-compose | uvicorn | custom
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
  dir: .retrodep
  screenshots: true
  html_report: true
```
