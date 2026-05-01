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
        # Find all Dockerfiles
        dockerfiles = list(repo.glob("**/Dockerfile*"))
        for df in dockerfiles:
            if self._patch_dockerfile(df):
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
                r"(\bnpm\s+ci\b)",
                r"(\bnpm\s+install\b)",
                r"(\byarn\s+install\b)",
                r"(\bpnpm\s+install\b)",
                r"(\bnpm\s+i\b)",
                r"(\bnpm\s+run\s+build\b)",
                r"(\bnpx\s+vite\s+build\b)",
                r"(\bvite\s+build\b)"
            ]
            
            for pattern in skip_patterns:
                # Replace command with 'true' to skip but keep shell syntax intact
                content = re.sub(pattern, "true", content, flags=re.IGNORECASE)
            
            # 2. Ensure node_modules are NOT deleted/overwritten if possible
            # (Usually just commenting out the install is enough as we COPY . .)
            
            if content != original:
                path.write_text(content)
                return True
        except Exception:
            pass
        return False
