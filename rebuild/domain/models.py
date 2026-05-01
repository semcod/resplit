from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional, Dict

class DeployMethod(Enum):
    AUTO = "auto"
    DOCKER_COMPOSE = "docker-compose"
    UVICORN = "uvicorn"
    NONE = "none"

@dataclass
class WalkConfig:
    repo_path: Path
    output_dir: Path = Path(".rebuild")
    days: int = 30
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    deploy_method: DeployMethod = DeployMethod.AUTO
    health_url: str = "http://localhost:8003/api/health"
    health_timeout: int = 60
    health_interval: int = 2
    health_verbose: bool = False
    deploy_retry_attempts: int = 1
    deploy_retry_backoff_seconds: float = 2.0
    deploy_retry_backoff_multiplier: float = 2.0
    base_url: str = "http://localhost:8003"
    screenshots: bool = True
    dry_run: bool = False
    compose_file: str = "docker-compose.yml"
    test_fixtures: Dict[str, str] = field(default_factory=dict)
    auth: Dict[str, str] = field(default_factory=dict)
    test_bodies: Dict[str, Dict] = field(default_factory=dict)
    login_url: Optional[str] = None  # URL to perform login and obtain token
    login_payload: Optional[Dict[str, str]] = None  # POST payload for login request
    
    # Phase 12: Replay Engine
    replay: bool = False
    app_service: Optional[str] = None  # Docker service to restart (e.g. 'backend')
    
    # Phase 13: 10x Accelerator Mode
    accelerator: bool = False  # Enable ultra-fast mode with worktrees + hot reload
    db_container: str = "db"  # Name of DB container for snapshots
    db_type: str = "postgres"  # postgres | mysql | sqlite
    max_parallel_tests: int = 10  # Max concurrent endpoint tests
    smart_select: bool = True  # Use git diff to select only affected tests
    keep_alive: bool = True  # Keep infrastructure running after walk
    shutdown_after: bool = False  # Override keep_alive and shutdown
