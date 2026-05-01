# Example 01 — Dry-run walk

Przejście przez ostatnie 30 dni historii git **bez deploy** (dry-run).
Przydatne do weryfikacji zakresu commitów i konfiguracji bez uruchamiania dockera.

## Uruchomienie

```bash
pip install resplit
resplit walk . --days 30 --dry-run --output .resplit
```

lub przez skrypt:

```bash
./run.sh /ścieżka/do/repo
```

## Co robi

1. Iteruje przez ostatnie 30 dni
2. Dla każdego dnia z commitem: wykrywa endpointy (bez deploy)
3. Zapisuje `endpoints.json` + `report.html` per dzień
4. Generuje `index.html` z timelineą

## Wynik

```
.resplit/
  2024-03-15/
    endpoints.json
    report.html
  2024-03-14/
    ...
  index.html
```
