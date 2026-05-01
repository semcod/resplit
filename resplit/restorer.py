"""
resplit.restorer — przywraca działający endpoint z historii git.

Workflow:
  1. Znajdź ostatni dzień, w którym endpoint zwracał status OK
  2. Checkout repo do tego commitu
  3. Wykryj pliki powiązane z endpointem (router, handler, template)
  4. Skopiuj do struktury:
       /nazwa-endpointu/
         frontend/   (jeśli wykryto)
         backend/    (handler + deps)
         docker/     (docker-compose + Dockerfile)
         README.md
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


def find_last_working_day(endpoint_path: str, results_dir: Path) -> Optional[date]:
    """
    Przeszukuje wyniki walk i zwraca ostatni dzień,
    w którym endpoint zwracał status OK.
    """
    best: Optional[date] = None

    for day_dir in sorted(results_dir.iterdir(), reverse=True):
        rf = day_dir / "results.json"
        if not rf.exists():
            continue
        try:
            day_date = date.fromisoformat(day_dir.name)
        except ValueError:
            continue

        results = json.loads(rf.read_text())
        for r in results:
            if r.get("path") == endpoint_path and r.get("status") == "ok":
                best = day_date
                break

        if best:
            break  # Już od najnowszego

    return best


def extract_endpoint(
    repo: Path,
    endpoint_path: str,
    working_day: date,
    target: Path,
) -> None:
    """
    Wyodrębnia endpoint do izolowanego projektu.

    Strategia:
    - Szuka pliku routera zawierającego ścieżkę endpointu
    - Kopiuje router + powiązane handlery
    - Kopiuje docker-compose + Dockerfile
    - Generuje README.md
    """
    target.mkdir(parents=True, exist_ok=True)

    # 1. Skopiuj docker/
    docker_dir = target / "docker"
    docker_dir.mkdir(exist_ok=True)
    for fname in ("docker-compose.yml", "docker-compose.yaml", "Dockerfile"):
        src = repo / fname
        if src.exists():
            shutil.copy2(src, docker_dir / fname)
    # Dockerfile w backend/
    for sub in ("backend", "frontend"):
        df = repo / sub / "Dockerfile"
        if df.exists():
            shutil.copy2(df, docker_dir / f"Dockerfile.{sub}")

    # 2. Skopiuj backend/
    backend_files = _find_backend_files(repo, endpoint_path)
    if backend_files:
        backend_dir = target / "backend"
        backend_dir.mkdir(exist_ok=True)
        for src in backend_files:
            rel = src.relative_to(repo)
            dst = backend_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        console.print(f"  Skopiowano {len(backend_files)} plików backend")

    # 3. Frontend (heurystyka: jeśli jest frontend/ i endpoint to strona)
    if _is_page_endpoint(endpoint_path) and (repo / "frontend").exists():
        frontend_dir = target / "frontend"
        shutil.copytree(repo / "frontend", frontend_dir, dirs_exist_ok=True)
        console.print("  Skopiowano frontend/")

    # 4. README
    _write_readme(target, endpoint_path, working_day, backend_files)
    console.print(f"  Zapisano README.md")


def _find_backend_files(repo: Path, endpoint_path: str) -> list[Path]:
    """
    Szuka plików Python/JS zawierających ścieżkę endpointu.
    Zwraca listę plików (router + bezpośrednie importy).
    """
    literal = endpoint_path
    pattern = re.compile(re.escape(literal))
    candidates: list[Path] = []

    for ext in ("*.py", "*.js", "*.ts", "*.jsx", "*.tsx"):
        for f in repo.rglob(ext):
            # Pomijamy node_modules, .venv, __pycache__
            if any(p in f.parts for p in ("node_modules", ".venv", "venv", "__pycache__", ".git")):
                continue
            try:
                content = f.read_text(errors="replace")
                if pattern.search(content):
                    candidates.append(f)
            except OSError:
                continue

    return candidates


def _is_page_endpoint(path: str) -> bool:
    """Heurystyka: czy endpoint to strona (brak /api/)"""
    return "/api/" not in path and "/webhook/" not in path


def _write_readme(
    target: Path,
    endpoint_path: str,
    working_day: date,
    backend_files: list[Path],
) -> None:
    slug = endpoint_path.strip("/").replace("/", "-") or "root"
    files_list = "\n".join(f"- `{f.name}`" for f in backend_files[:10])

    readme = f"""# Przywrócony endpoint: `{endpoint_path}`

Wyodrębniony z historii git — ostatni działający dzień: **{working_day}**

Wygenerowany przez [resplit](https://github.com/semcod/resplit).

## Struktura

```
{slug}/
  backend/    # handlery i router endpointu
  frontend/   # (jeśli dotyczy)
  docker/     # docker-compose + Dockerfile
  README.md
```

## Znalezione pliki backend

{files_list or "_(brak)_"}

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
GET http://localhost:8003{endpoint_path}
```
"""
    (target / "README.md").write_text(readme, encoding="utf-8")
