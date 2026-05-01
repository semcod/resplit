# Example 02 — Docker Compose project walk

Pełny walk z deployem przez `docker compose` + health check + screenshoty.
Wzorcowy przypadek dla projektów FastAPI / Django z `docker-compose.yml`.

## Wymagania

- Docker + Docker Compose v2
- `pip install resplit[screenshots]` (Playwright)
- Projekt z `docker-compose.yml` i endpointem health na porcie 8003

## Struktura projektu (oczekiwana)

```
my-project/
  docker-compose.yml
  backend/
    server.py       ← FastAPI app
    Dockerfile
  frontend/
    ...
```

## Uruchomienie

```bash
pip install "resplit[screenshots]"
playwright install chromium

./run.sh /ścieżka/do/my-project
```

## Konfiguracja

Edytuj `resplit.yaml` aby dostosować:
- `health_url` — URL health check po deploy
- `days` — zakres historii
- `base_url` — bazowy URL usługi

## Wynik

```
.resplit/
  2024-03-15/
    commit.txt
    endpoints.json
    results.json
    report.html
    screenshots/
      GET_api_health.png
      GET_api_items.png
  index.html
  dashboard.html    ← po uruchomieniu: resplit dashboard
```
