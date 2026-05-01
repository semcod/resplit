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
            
            # 1. Comment out npm install / npm ci / yarn install / pnpm install
            # Matches: RUN npm ci, RUN npm install, etc.
            install_patterns = [
                r"(RUN\s+npm\s+ci)",
                r"(RUN\s+npm\s+install)",
                r"(RUN\s+yarn\s+install)",
                r"(RUN\s+pnpm\s+install)",
                r"(RUN\s+npm\s+i\s)"
            ]
            
            for pattern in install_patterns:
                content = re.sub(pattern, r"# \1 (Patched by rebuild accelerator)", content, flags=re.IGNORECASE)
            
            # 2. Ensure node_modules are NOT deleted/overwritten if possible
            # (Usually just commenting out the install is enough as we COPY . .)
            
            if content != original:
                path.write_text(content)
                return True
        except Exception:
            pass
        return False
