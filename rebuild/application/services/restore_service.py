from __future__ import annotations
import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from rich.console import Console
from .base import Service

class RestoreService(Service[Tuple[str, Path], Optional[date]]):
    """
    Service for restoring a working endpoint from git history.
    """
    def __init__(self, repo_path: Path, console: Optional[Console] = None):
        self.repo_path = repo_path
        self.console = console or Console()

    def execute(self, input: Tuple[str, Path]) -> Optional[date]:
        """
        Finds the last working day for an endpoint.
        """
        endpoint_path, results_dir = input
        return self.find_last_working_day(endpoint_path, results_dir)

    def find_last_working_day(self, endpoint_path: str, results_dir: Path) -> Optional[date]:
        best: Optional[date] = None
        if not results_dir.exists():
            return None

        for day_dir in sorted(results_dir.iterdir(), reverse=True):
            rf = day_dir / "results.json"
            if not rf.exists():
                continue
            try:
                day_date = date.fromisoformat(day_dir.name)
            except ValueError:
                continue

            data = json.loads(rf.read_text())
            # Handle both old (list) and new (dict) schemas
            results = data.get("results", []) if isinstance(data, dict) else data
            
            for r in results:
                if r.get("path") == endpoint_path and r.get("status") == "ok":
                    best = day_date
                    break

            if best:
                break

        return best

    def extract_endpoint(self, endpoint_path: str, working_day: date, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)

        docker_dir = target / "docker"
        docker_dir.mkdir(exist_ok=True)
        for fname in ("docker-compose.yml", "docker-compose.yaml", "Dockerfile"):
            src = self.repo_path / fname
            if src.exists():
                shutil.copy2(src, docker_dir / fname)
        
        for sub in ("backend", "frontend"):
            df = self.repo_path / sub / "Dockerfile"
            if df.exists():
                shutil.copy2(df, docker_dir / f"Dockerfile.{sub}")

        backend_files = self._find_backend_files(endpoint_path)
        if backend_files:
            backend_dir = target / "backend"
            backend_dir.mkdir(exist_ok=True)
            for src in backend_files:
                rel = src.relative_to(self.repo_path)
                dst = backend_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            self.console.print(f"  Skopiowano {len(backend_files)} plików backend")

        if self._is_page_endpoint(endpoint_path) and (self.repo_path / "frontend").exists():
            frontend_dir = target / "frontend"
            shutil.copytree(self.repo_path / "frontend", frontend_dir, dirs_exist_ok=True)
            self.console.print("  Skopiowano frontend/")

        self._write_readme(target, endpoint_path, working_day, backend_files)
        self.console.print(f"  Zapisano README.md")

    def _find_backend_files(self, endpoint_path: str) -> List[Path]:
        literal = endpoint_path
        pattern = re.compile(re.escape(literal))
        candidates: List[Path] = []

        for ext in ("*.py", "*.js", "*.ts", "*.jsx", "*.tsx"):
            for f in self.repo_path.rglob(ext):
                if any(p in f.parts for p in ("node_modules", ".venv", "venv", "__pycache__", ".git")):
                    continue
                try:
                    content = f.read_text(errors="replace")
                    if pattern.search(content):
                        candidates.append(f)
                except OSError:
                    continue
        return candidates

    def _is_page_endpoint(self, path: str) -> bool:
        return "/api/" not in path and "/webhook/" not in path

    def _write_readme(self, target: Path, endpoint_path: str, working_day: date, backend_files: List[Path]) -> None:
        slug = endpoint_path.strip("/").replace("/", "-") or "root"
        files_list = "\n".join(f"- `{f.name}`" for f in backend_files[:10])

        readme = f"""# Przywrócony endpoint: `{endpoint_path}`

Wyodrębniony z historii git — ostatni działający dzień: **{working_day}**

Wygenerowany przez [rebuild](https://github.com/semcod/rebuild).

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
