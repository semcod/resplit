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
        """Removes fixed names from networks/volumes to avoid collisions."""
        try:
            content = path.read_text()
            original = content
            
            # Remove 'name: ...' under 'networks:' and 'volumes:'
            # But ONLY if it's inside the 'networks' or 'volumes' top-level keys
            # To be safe and simple, we'll use regex to find 'name:' followed by names we know cause trouble
            # or just any 'name:' under a network definition.
            
            # Pattern: any line with 'name:' that is preceded by a few spaces (not top level)
            content = re.sub(r'^\s+name:\s+.*$', '', content, flags=re.MULTILINE)
            
            # Also remove 'container_name:' to allow parallel runs
            content = re.sub(r'^\s+container_name:\s+.*$', '', content, flags=re.MULTILINE)
            
            # Remove Traefik Host rules that might conflict
            content = re.sub(r'Host\(`[^`]+`\)', 'Host(`localhost`)', content)

            if content != original:
                path.write_text(content)
                return True
        except Exception:
            pass
        return False
