"""
Database snapshot/restore for instant state reset.
Eliminates DB seed time between test runs.
"""
from __future__ import annotations
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .base import Service
from ...infrastructure.shell_adapter import ShellAdapter


@dataclass
class SnapshotInfo:
    """Metadata about a database snapshot."""
    name: str
    created_at: str
    commit_sha: Optional[str] = None
    size_bytes: Optional[int] = None
    db_type: str = "postgres"  # postgres, mysql, sqlite, etc.


class DBSnapshotManager(Service[str, SnapshotInfo]):
    """
    Manages database snapshots for instant state restore.
    
    Instead of re-seeding DB for each test run:
    1. Create base snapshot once (pg_dump, volume export, etc.)
    2. Restore snapshot instantly for each commit
    3. Massive speedup for test suites
    """
    
    def __init__(
        self,
        snapshot_dir: Path,
        db_container: str = "db",
        db_type: str = "postgres",
        db_name: str = "app",
        db_user: str = "postgres",
        shell: Optional[ShellAdapter] = None,
        ready_timeout: int = 30,
        ready_interval: float = 1.0,
    ):
        self.snapshot_dir = snapshot_dir
        self.db_container = db_container
        self.db_type = db_type
        self.db_name = db_name
        self.db_user = db_user
        self.shell = shell or ShellAdapter()
        self.ready_timeout = ready_timeout
        self.ready_interval = ready_interval
        self._metadata_file = snapshot_dir / "snapshots.json"
        self._snapshots: Dict[str, SnapshotInfo] = {}
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create snapshot directory structure."""
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._load_metadata()
    
    def _load_metadata(self):
        """Load snapshot metadata from disk."""
        if self._metadata_file.exists():
            try:
                data = json.loads(self._metadata_file.read_text())
                for name, info in data.items():
                    self._snapshots[name] = SnapshotInfo(**info)
            except Exception:
                pass
    
    def _save_metadata(self):
        """Persist snapshot metadata."""
        data = {name: asdict(info) for name, info in self._snapshots.items()}
        self._metadata_file.write_text(json.dumps(data, indent=2))
    
    def create(self, name: str, commit_sha: Optional[str] = None) -> SnapshotInfo:
        """
        Create a new database snapshot.
        """
        snapshot_path = self.snapshot_dir / f"{name}.sql"
        
        if self.db_type == "postgres":
            self._postgres_dump(snapshot_path)
        elif self.db_type == "mysql":
            self._mysql_dump(snapshot_path)
        elif self.db_type == "sqlite":
            self._sqlite_dump(snapshot_path)
        else:
            raise ValueError(f"Unsupported DB type: {self.db_type}")
        
        # Get file size
        size = snapshot_path.stat().st_size if snapshot_path.exists() else 0
        
        info = SnapshotInfo(
            name=name,
            created_at=datetime.now().isoformat(),
            commit_sha=commit_sha,
            size_bytes=size,
            db_type=self.db_type
        )
        
        self._snapshots[name] = info
        self._save_metadata()
        return info
    
    def _postgres_dump(self, output_path: Path):
        """Create PostgreSQL dump using pg_dump in container."""
        cmd = [
            "docker", "exec", self.db_container,
            "pg_dump", "-U", self.db_user, "-d", self.db_name,
            "-f", "/tmp/snapshot.sql"
        ]
        result = self.shell.run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")
        
        # Copy from container to host
        self.shell.run([
            "docker", "cp",
            f"{self.db_container}:/tmp/snapshot.sql",
            str(output_path)
        ])
    
    def _mysql_dump(self, output_path: Path):
        """Create MySQL dump."""
        cmd = [
            "docker", "exec", self.db_container,
            "mysqldump", "-u", self.db_user, self.db_name
        ]
        result = self.shell.run(cmd)
        if result.returncode == 0:
            output_path.write_text(result.stdout)
        else:
            raise RuntimeError(f"mysqldump failed: {result.stderr}")
    
    def _sqlite_dump(self, output_path: Path):
        """Create SQLite backup."""
        # For SQLite, we can just copy the file from volume
        volume_path = f"{self.db_container}:/app/data.db"
        self.shell.run(["docker", "cp", volume_path, str(output_path)])
    
    def restore(self, name: str, quick: bool = False) -> bool:
        """
        Restore database from snapshot.
        
        Args:
            name: Snapshot name
            quick: If True, use volume-level restore (faster but more destructive)
        """
        if name not in self._snapshots:
            raise ValueError(f"Snapshot '{name}' not found")
        
        snapshot_path = self.snapshot_dir / f"{name}.sql"
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot file missing: {snapshot_path}")
        
        if quick and self.db_type == "postgres":
            restored = self._quick_restore_postgres(snapshot_path)
        elif self.db_type == "postgres":
            restored = self._postgres_restore(snapshot_path)
        elif self.db_type == "mysql":
            restored = self._mysql_restore(snapshot_path)
        elif self.db_type == "sqlite":
            restored = self._sqlite_restore(snapshot_path)
        else:
            restored = False

        if not restored:
            return False

        return self._wait_until_ready()

    def _wait_until_ready(self) -> bool:
        """Wait until the restored database is ready to accept connections."""
        if self.db_type == "sqlite":
            return True

        deadline = time.time() + self.ready_timeout
        while time.time() < deadline:
            result = self.shell.run(self._ready_check_command())
            if result.returncode == 0:
                return True
            time.sleep(self.ready_interval)
        return False

    def _ready_check_command(self) -> list[str]:
        if self.db_type == "postgres":
            return [
                "docker", "exec", self.db_container,
                "pg_isready", "-U", self.db_user, "-d", self.db_name,
            ]
        if self.db_type == "mysql":
            return [
                "docker", "exec", self.db_container,
                "mysqladmin", "ping", "-u", self.db_user, "--silent",
            ]
        return ["true"]
    
    def _postgres_restore(self, snapshot_path: Path) -> bool:
        """Restore PostgreSQL from SQL dump."""
        # Copy dump to container
        cp_result = self.shell.run([
            "docker", "cp", str(snapshot_path),
            f"{self.db_container}:/tmp/restore.sql"
        ])
        if cp_result.returncode != 0:
            return False
        
        # Restore - terminate connections first, then restore
        cmds = [
            # Drop and recreate DB (fastest for test scenarios)
            ["docker", "exec", self.db_container, "psql", "-U", self.db_user, "-d", "postgres", "-c", 
             f"DROP DATABASE IF EXISTS {self.db_name}; CREATE DATABASE {self.db_name};"],
            # Restore data
            ["docker", "exec", self.db_container, "psql", "-U", self.db_user, "-d", self.db_name, "-f", "/tmp/restore.sql"]
        ]
        
        for cmd in cmds:
            result = self.shell.run(cmd)
            if result.returncode != 0:
                print(f"Restore warning: {result.stderr[:200]}")
        
        return True
    
    def _quick_restore_postgres(self, snapshot_path: Path) -> bool:
        """
        Ultra-fast restore using volume manipulation.
        Stops container, replaces volume data, starts container.
        """
        # Get volume name
        result = self.shell.run([
            "docker", "inspect", "-f", "{{ range .Mounts }}{{ if eq .Type \"volume\" }}{{ .Name }}{{ end }}{{ end }}",
            self.db_container
        ])
        volume_name = result.stdout.strip()
        
        if not volume_name:
            # Fallback to regular restore
            return self._postgres_restore(snapshot_path)
        
        # Stop container
        self.shell.run(["docker", "stop", self.db_container])
        
        # Run postgres in temporary container to load data
        load_cmd = [
            "docker", "run", "--rm",
            "-v", f"{volume_name}:/var/lib/postgresql/data",
            "-v", f"{snapshot_path}:/restore.sql",
            "postgres:15",
            "bash", "-c",
            f"rm -rf /var/lib/postgresql/data/* && pg_ctl initdb -D /var/lib/postgresql/data && "
            f"pg_ctl start -D /var/lib/postgresql/data && "
            f"psql -U postgres -f /restore.sql"
        ]
        result = self.shell.run(load_cmd)
        
        # Start original container
        self.shell.run(["docker", "start", self.db_container])
        
        return result.returncode == 0
    
    def _mysql_restore(self, snapshot_path: Path) -> bool:
        """Restore MySQL database."""
        cp_result = self.shell.run([
            "docker", "cp", str(snapshot_path),
            f"{self.db_container}:/tmp/restore.sql"
        ])
        if cp_result.returncode != 0:
            return False
        
        result = self.shell.run([
            "docker", "exec", self.db_container,
            "mysql", "-u", self.db_user, self.db_name,
            "-e", "source /tmp/restore.sql"
        ])
        return result.returncode == 0
    
    def _sqlite_restore(self, snapshot_path: Path) -> bool:
        """Restore SQLite database."""
        result = self.shell.run([
            "docker", "cp", str(snapshot_path),
            f"{self.db_container}:/app/data.db"
        ])
        return result.returncode == 0
    
    def create_baseline(self, commit_sha: Optional[str] = None) -> SnapshotInfo:
        """Create a baseline snapshot (e.g., after migrations, before seed)."""
        name = "baseline" if not commit_sha else f"baseline_{commit_sha[:8]}"
        return self.create(name, commit_sha)
    
    def list_snapshots(self) -> Dict[str, SnapshotInfo]:
        """List all available snapshots."""
        return dict(self._snapshots)
    
    def delete(self, name: str) -> bool:
        """Delete a snapshot."""
        snapshot_path = self.snapshot_dir / f"{name}.sql"
        if snapshot_path.exists():
            snapshot_path.unlink()
        
        if name in self._snapshots:
            del self._snapshots[name]
            self._save_metadata()
        
        return True
    
    def execute(self, action: str) -> SnapshotInfo:
        """Service interface: create baseline snapshot."""
        if action == "baseline":
            return self.create_baseline()
        raise ValueError(f"Unknown action: {action}")
