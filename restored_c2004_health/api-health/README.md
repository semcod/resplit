# Przywrócony endpoint: `/api/health`

Wyodrębniony z historii git — ostatni działający dzień: **2026-04-30**

Wygenerowany przez [rebuild](https://github.com/semcod/rebuild).

## Struktura

```
api-health/
  backend/    # handlery i router endpointu
  frontend/   # (jeśli dotyczy)
  docker/     # docker-compose + Dockerfile
  README.md
```

## Znalezione pliki backend

- `main.py`
- `main.py`
- `main.py`
- `main.py`
- `vite.config.js`
- `main.js`
- `module-smoke-test-template.spec.ts`
- `all-modules-smoke.spec.ts`

## Uruchomienie

```bash
# Opcja 1: docker-compose
cd docker/
docker compose up -d

# Opcja 2: lokalnie
cd backend/
pip install -r requirements.txt
uvicorn server:app --reload --port 8003
```

## Endpoint

```
GET http://localhost:8003/api/health
```
