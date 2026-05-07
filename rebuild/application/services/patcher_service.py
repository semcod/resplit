from __future__ import annotations
from pathlib import Path
import re
import shutil
from .base import Service

class PatcherService(Service[Path, int]):
    """
    Service for patching files in the repo clone.
    Used in Accelerator Mode to skip expensive/failing steps like npm install.
    """
    def execute(self, repo: Path) -> int:
        patched_count = 0
        # 1. Patch Dockerfiles
        dockerfiles = list(repo.glob("**/Dockerfile*"))
        for df in dockerfiles:
            if self._patch_dockerfile(df):
                patched_count += 1

        # 2. Patch docker-compose files
        compose_files = list(repo.glob("**/docker-compose*.yml")) + list(repo.glob("**/docker-compose*.yaml"))
        for cf in compose_files:
            if self._patch_compose(cf):
                patched_count += 1

        return patched_count

    def apply_manual_overrides(self, patch_dir: Path, repo: Path) -> int:
        """
        Overlays files from patch_dir onto repo preserving relative paths.
        This enables manual hot-fixes in `.rebuild/patch/` without touching source repo.
        """
        if not patch_dir.exists() or not patch_dir.is_dir():
            return 0

        applied = 0
        for src in patch_dir.rglob("*"):
            if not src.is_file():
                continue

            rel = src.relative_to(patch_dir)
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            applied += 1

        return applied

    def _patch_dockerfile(self, path: Path) -> bool:
        try:
            content = path.read_text()
            original = content

            # 1. Comment out install and build commands
            # Matches: RUN npm ci, RUN npm install, RUN npm run build, RUN npx vite build, etc.
            skip_patterns = [
                (r"(\bnpm\s+ci\b)", "true"),
                (r"(\bnpm\s+install\b)", "true"),
                (r"(\byarn\s+install\b)", "true"),
                (r"(\bpnpm\s+install\b)", "true"),
                (r"(\bnpm\s+i\b)", "true"),
                (r"(\bnpm\s+run\s+build\b)", "true && mkdir -p dist build out"),
                (r"(\bnpx\s+vite\s+build\b)", "true && mkdir -p dist build out"),
                (r"(\bvite\s+build\b)", "true && mkdir -p dist build out")
            ]

            for pattern, replacement in skip_patterns:
                # Replace command with 'true' to skip but keep shell syntax intact
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

            # 2. Ensure node_modules are NOT deleted/overwritten if possible
            # (Usually just commenting out the install is enough as we COPY . .)

            if content != original:
                path.write_text(content)
                return True
        except Exception:
            pass
    def _patch_compose(self, path: Path) -> bool:
        """Removes fixed names and DB ports to avoid collisions."""
        try:
            content = path.read_text()
            original = content

            # 1. Remove fixed names (networks, volumes, containers)
            content = re.sub(r'^\s+name:\s+.*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'^\s+container_name:\s+.*$', '', content, flags=re.MULTILINE)

            # 2. Remove common DB port bindings to avoid host collisions
            # Matches: postgres:, db:, redis:, etc followed by ports: - "5432:5432"
            db_services = ["postgres", "db", "redis", "mysql", "mariadb", "mongo", "mongodb"]
            for svc in db_services:
                # Find the service block and the ports section within it
                # This is a bit rough with regex but usually works for standard compose
                pattern = rf'({svc}:.*?\n\s+ports:\n\s+-\s+["\']?\d+:\d+["\']?)'
                content = re.sub(pattern, r'\1 # patched by rebuild', content, flags=re.DOTALL | re.IGNORECASE)
                # Actually, just comment out the whole ports block for these
                content = re.sub(rf'({svc}:.*?)(\n\s+ports:\n\s+-\s+["\']?\d+:\d+["\']?)', r'\1\n# \2', content, flags=re.DOTALL | re.IGNORECASE)

            # 3. Remove Traefik Host rules
            content = re.sub(r'Host\(`[^`]+`\)', 'Host(`localhost`)', content)

            if content != original:
                path.write_text(content)
                return True
        except Exception:
            pass
        return False
