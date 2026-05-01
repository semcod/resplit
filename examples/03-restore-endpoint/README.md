# Example 03 — Restore endpoint

Przywrócenie działającego endpointu jako izolowany projekt.
Używane gdy endpoint przestał działać i chcemy wyciągnąć ostatnią działającą wersję.

## Workflow

```
rebuild walk (wcześniej)  →  .rebuild/ z wynikami per dzień
          ↓
rebuild restore /api/health  →  restored/api-health/
                                  backend/
                                  docker/
                                  README.md
```

## Wymagania

- Wcześniej uruchomiony `rebuild walk` (wyniki w `.rebuild/`)
- Repozytorium dostępne lokalnie

## Uruchomienie

```bash
# Krok 1: znajdź ostatni działający dzień dla endpointu
rebuild restore /api/health . --output ./restored

# Krok 2: uruchom przywrócony projekt
cd restored/api-health/docker
docker compose up -d
curl http://localhost:8003/api/health
```

lub przez skrypt:

```bash
./run.sh /api/health /ścieżka/do/repo ./restored
```

## Wynik

```
restored/
  api-health/
    backend/
      server.py       ← skopiowany z działającego commitu
      router.py
    docker/
      docker-compose.yml
      Dockerfile
    README.md         ← instrukcja uruchomienia
```

## Co robi rebuild restore

1. Przeszukuje `.rebuild/*/results.json` od najnowszego dnia
2. Znajduje ostatni dzień gdzie endpoint zwracał `status: ok`
3. Checkout repo do tego commitu
4. Kopiuje pliki backend (heurystyka: pliki zawierające ścieżkę endpointu)
5. Kopiuje `docker-compose.yml` + `Dockerfile`
6. Generuje `README.md` z instrukcją uruchomienia
