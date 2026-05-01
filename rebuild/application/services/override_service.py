from __future__ import annotations
from pathlib import Path
import shutil
from .base import Service

class OverrideService(Service[Path, int]):
    """
    Service for applying manual overrides (patches) to the repo clone.
    Allows fixing historical bugs by copying files from a patch directory.
    """
    def execute(self, repo: Path, patch_source: Optional[Path] = None) -> int:
        if not patch_source or not patch_source.exists():
            return 0
        
        overridden_count = 0
        # Iterate over all files in patch_source recursively
        for patch_file in patch_source.rglob("*"):
            if patch_file.is_file():
                # Calculate relative path from patch_source
                rel_path = patch_file.relative_to(patch_source)
                target_file = repo / rel_path
                
                # Ensure target directory exists
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file to clone
                shutil.copy2(patch_file, target_file)
                overridden_count += 1
                
        return overridden_count
